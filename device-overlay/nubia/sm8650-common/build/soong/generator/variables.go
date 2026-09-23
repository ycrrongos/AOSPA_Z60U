package generator

import (
	"fmt"

	"android/soong/android"
)

func cerroExpandVariables(ctx android.ModuleContext, in string) string {
	cerroVars := ctx.Config().VendorConfig("cerroVarsPlugin")

	out, err := android.Expand(in, func(name string) (string, error) {
		if cerroVars.IsSet(name) {
			return cerroVars.String(name), nil
		}
		return fmt.Sprintf("$(%s)", name), nil
	})

	if err != nil {
		ctx.PropertyErrorf("%s: %s", in, err.Error())
		return ""
	}

	return out
}
