{
  description = "bitranox_template_py_cli Nix flake";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        lib = pkgs.lib;
        pypkgs = pkgs.python310Packages;

        hatchlingVendor = pypkgs.buildPythonPackage rec {
          pname = "hatchling";
          version = "1.25.0";
          format = "wheel";
          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/py3/h/hatchling/hatchling-1.25.0-py3-none-any.whl";
            hash = "sha256-tHlI5F1NlzA0WE3UyznBS2pwInzyh6t+wK15g0CKiCw";
          };
          propagatedBuildInputs = [
            pypkgs.packaging
            pypkgs.tomli
            pypkgs.pathspec
            pypkgs.pluggy
            pypkgs."trove-classifiers"
            pypkgs.editables
          ];
          doCheck = false;
        };
        clickVendor = pypkgs.buildPythonPackage rec {
          pname = "click";
          version = "8.3.0";
          format = "wheel";
          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/db/d3/9dcc0f5797f070ec8edf30fbadfb200e71d9db6b84d211e3b2085a7589a0/click-8.3.0-py3-none-any.whl";
            sha256 = "sha256-m58oUwLG4wZPQzDAXwW4GUWyo5VEJ5ND5ufF8nqbrdw=";
          };
          doCheck = false;
        };

        libCliExitToolsVendor = pypkgs.buildPythonPackage rec {
          pname = "lib_cli_exit_tools";
          version = "1.1.1";
          format = "wheel";
          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/78/a9/3a3eb69c3fe8f2fc0d659600e38ae2f0334507cbbef383fd628038a8f779/lib_cli_exit_tools-1.1.1-py3-none-any.whl";
            sha256 = "sha256-MX0896kKVwphlsTLkAPYLAYhyZE9Ajpi4xbmMhLBchY=";
          };
          doCheck = false;
        };

        richVendor = pypkgs.buildPythonPackage rec {
          pname = "rich";
          version = "14.1";
          format = "wheel";
          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/e3/30/3c4d035596d3cf444529e0b2953ad0466f6049528a879d27534700580395/rich-14.1.0-py3-none-any.whl";
            sha256 = "sha256-U29fF4WYbW296jx1IFxHP5cHd7Sg1sbdG2lqoFo/oE8=";
          };
          doCheck = false;
        };

      in
      {
        packages.default = pypkgs.buildPythonPackage {
          pname = "bitranox_template_py_cli";
          version = "1.4.0";
          pyproject = true;
          src = ../..;
          nativeBuildInputs = [ hatchlingVendor ];
          propagatedBuildInputs = [ clickVendor libCliExitToolsVendor richVendor ];

          meta = with pkgs.lib; {
            description = "Rich-powered logging helpers for colorful terminal output";
            homepage = "https://github.com/bitranox/bitranox_template_py_cli";
            license = licenses.mit;
            maintainers = [];
            platforms = platforms.unix ++ platforms.darwin;
          };
        };

        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.python310
            hatchlingVendor
            clickVendor
            libCliExitToolsVendor
            richVendor
            pypkgs.pytest
            pkgs.ruff
            pkgs.nodejs
          ];
        };
      }
    );
}
