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

        # Vendor hatchling>=1.25 from PyPI (wheel) to satisfy PEP 517 build
        hatchlingVendor = pypkgs.buildPythonPackage rec {
          pname = "hatchling";
          version = "1.25.0";
          format = "wheel"; # install straight from wheel to avoid circular build-backend
          # Use explicit URL for py3 wheel; nixpkgs 24.05 fetchPypi may choose a py2.py3 path.
          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/py3/h/hatchling/${pname}-${version}-py3-none-any.whl";
            hash = "sha256-tHlI5F1NlzA0WE3UyznBS2pwInzyh6t+wK15g0CKiCw=";
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

        libCliExitTools = pypkgs.buildPythonPackage rec {
          pname = "lib_cli_exit_tools";
          version = "1.1.1";
          format = "wheel";
          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/py3/l/lib_cli_exit_tools/${pname}-${version}-py3-none-any.whl";
            hash = "sha256-MX0896kKVwphlsTLkAPYLAYhyZE9Ajpi4xbmMhLBchY=";
          };
          doCheck = false;
        };

        clickLatest = pypkgs.buildPythonPackage rec {
          pname = "click";
          version = "8.1";
          format = "wheel";
          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/py3/c/click/click-8.3.0-py3-none-any.whl";
            sha256 = "sha256-GaS6pk2pJMXgzYiauo6UfygDCfGizglHo+OnvLfMctY=";
          };
          doCheck = false;
        };

        richLatest = pypkgs.buildPythonPackage rec {
          pname = "rich";
          version = "13.7";
          format = "wheel";
          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/py3/r/rich/rich-14.1.0-py3-none-any.whl";
            sha256 = "sha256-baFMEIxIZu6VILv/px9v45YuGTt9pocgWDhQzUVI4jU=";
          };
          doCheck = false;
        };
      in
      {
        packages.default = pypkgs.buildPythonPackage {
          pname = "bitranox_template_py_cli";
          version = "1.4.0";
          pyproject = true;
          # Build from the repository root (two levels up from packaging/nix)
          src = ../..;
          # For pinned releases, swap src for fetchFromGitHub with a rev/sha256.
          # src = pkgs.fetchFromGitHub {
          #   owner = "bitranox";
          #   repo = "bitranox_template_py_cli";
          #   rev = "v1.4.0";
          #   sha256 = "<fill-me>";
          # };

          # Ensure PEP 517 backend is available at required version
          # Ensure PEP 517 backend available at required version (>=1.25)
          nativeBuildInputs = [ hatchlingVendor ];
          propagatedBuildInputs = [ richLatest clickLatest libCliExitTools ];

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
            richLatest
            clickLatest
            libCliExitTools
            pypkgs.pytest
            pkgs.ruff
            pkgs.nodejs
          ];
        };
      }
    );
}
