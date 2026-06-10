{
  description = "Python development environment for Human-Computable-Passwords";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, utils }:
    utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config = {
            allowUnfree = true;
          };
        };
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          numpy
          pandas
          matplotlib
          scikit-learn
          tensorflow
          keras
          google-genai
          requests
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
          ];
        };
      }
    );
}
