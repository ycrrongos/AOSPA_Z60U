// Copyright 2015 Google Inc. All rights reserved.
// Copyright (C) 2018 The LineageOS Project
//
// AOSPA cerro: Voltage/Lineage soong generator, retargeted (cerro_generator).
// Used to run kernel headers_install for generated_kernel_includes.

package generator

import (
	"fmt"
	"path/filepath"
	"strings"

	"github.com/google/blueprint/proptools"

	"android/soong/android"
)

func init() {
	android.RegisterModuleType("cerro_generator", GeneratorFactory)
}

var String = proptools.String

var (
	pctx = android.NewPackageContext("android/soong/cerro/generator")
)

type generatorProperties struct {
	Cmd *string

	Export_include_dirs []string
	Export_source_dirs  []string

	Dep_root *string
	Dep_files []string
}

type Module struct {
	android.ModuleBase

	properties generatorProperties

	exportedIncludeDirs android.Paths
	exportedSourceDirs  android.Paths
	outputDeps          android.Paths
	inputDeps           android.Paths
}

func (g *Module) GeneratedHeaderDirs() android.Paths {
	return g.exportedIncludeDirs
}

func (g *Module) GeneratedSourceFiles() android.Paths {
	return g.exportedSourceDirs
}

func (g *Module) GeneratedDeps() android.Paths {
	return g.outputDeps
}

func (g *Module) DepsMutator(ctx android.BottomUpMutatorContext) {
	android.ExtractSourcesDeps(ctx, g.properties.Dep_files)
}

func (g *Module) GenerateAndroidBuildActions(ctx android.ModuleContext) {
	if len(g.properties.Export_include_dirs) > 0 {
		for _, dir := range g.properties.Export_include_dirs {
			g.exportedIncludeDirs = append(g.exportedIncludeDirs,
				android.PathForModuleGen(ctx, dir))
		}
	} else {
		g.exportedIncludeDirs = append(g.exportedIncludeDirs, android.PathForModuleGen(ctx, ""))
	}
	if len(g.properties.Export_source_dirs) > 0 {
		for _, dir := range g.properties.Export_source_dirs {
			g.exportedSourceDirs = append(g.exportedSourceDirs,
				android.PathForModuleGen(ctx, dir))
		}
	} else {
		g.exportedSourceDirs = append(g.exportedSourceDirs, android.PathForModuleGen(ctx, ""))
	}

	depRoot := String(g.properties.Dep_root)
	if depRoot == "" {
		depRoot = ctx.ModuleDir()
	} else {
		depRoot = cerroExpandVariables(ctx, depRoot)
	}

	for _, dep_file := range g.properties.Dep_files {
		dep_file = cerroExpandVariables(ctx, dep_file)
		globPath := filepath.Join(depRoot, dep_file)
		paths, err := ctx.GlobWithDeps(globPath, nil)
		if err != nil {
			ctx.ModuleErrorf("unable to glob %s: %s", globPath, err.Error())
			return
		}
		for _, path := range paths {
			if strings.HasSuffix(path, "/") {
				continue
			}
			g.inputDeps = append(g.inputDeps, android.PathForSource(ctx, path))
		}
	}

	exCmd := cerroExpandVariables(ctx, String(g.properties.Cmd))
	dummyDep := android.PathForModuleGen(ctx, ".dummy_dep")
	genDir := android.PathForModuleGen(ctx)
	manifestPath := android.PathForModuleOut(ctx, "cerro.sbox.textproto")

	rule := android.NewRuleBuilder(pctx, ctx).Sbox(genDir, manifestPath)
	rule.Command().Text("touch").Output(dummyDep)
	cmd := rule.Command()

	rawCommand, err := android.Expand(exCmd, func(name string) (string, error) {
		switch name {
		case "genDir":
			return android.PathForModuleGen(ctx).String(), nil
		default:
			return "", fmt.Errorf("unknown variable '$(%s)'", name)
		}
	})
	if err != nil {
		ctx.PropertyErrorf("cmd", "%s", err.Error())
		return
	}

	cmd.Text(rawCommand)
	cmd.ImplicitOutput(dummyDep)
	cmd.Implicits(g.inputDeps)

	g.outputDeps = append(g.outputDeps, dummyDep)
	rule.Build("generator", "generate")
}

func NewGenerator() *Module {
	module := &Module{}
	module.AddProperties(&module.properties)
	return module
}

func GeneratorFactory() android.Module {
	m := NewGenerator()
	android.InitAndroidModule(m)
	return m
}
