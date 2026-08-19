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
            # 週次報告のPDF組版（docs/reports/*.md -> pdf）
            pkgs.pandoc   # Markdown を読み，Typst 経由で PDF を出す
            pkgs.typst    # 組版エンジン
            pkgs.entr     # 保存を検知して自動で再ビルド（make report-watch）
            # 和文フォント。システムの Noto CJK は可変フォント（VF）で，Typst は
            # VF に未対応のため太字が出ない。Source Han は同じ書体の静的版で，
            # Regular / Bold / Heavy を実際に持っているのでこちらを使う。
            pkgs.source-han-serif
            pkgs.source-han-sans
          ];
          shellHook = ''
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:/run/opengl-driver/lib:$LD_LIBRARY_PATH"
            # Typst にフォントの在り処を教える（fontconfig 任せだとVF版を拾ってしまう）
            export TYPST_FONT_PATHS="${pkgs.source-han-serif}/share/fonts:${pkgs.source-han-sans}/share/fonts''${TYPST_FONT_PATHS:+:$TYPST_FONT_PATHS}"
          '';
        };
      }
    );
}
