let
  # Use `niv update` to update nixpkgs.
  # See https://github.com/nmattia/niv/
  sources = import ./nix/sources.nix;

  #pkgs = import sources.nixpkgs { config.allowUnfree = true; overlays = [ easyocrOverlay ]; };
  pkgs = import sources.nixpkgs { config.allowUnfree = true; overlays = [ ]; };

  my-python = pkgs.python3.withPackages (p: with p; [
    click
    dulwich
    defusedxml
    hiredis
    pyyaml
    redis
    requests
  ]);
    
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    my-python
  ];
}
