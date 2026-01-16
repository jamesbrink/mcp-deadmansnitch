{
  lib,
  python3Packages,
  src ? null,
}:
python3Packages.buildPythonApplication rec {
  pname = "mcp-deadmansnitch";
  version = "0.1.1";
  pyproject = true;

  # Source is passed in from flake.nix using `self`
  inherit src;

  build-system = with python3Packages; [
    hatchling
  ];

  dependencies = with python3Packages; [
    fastmcp
    httpx
    python-dotenv
    # Transitive deps needed at runtime but not auto-propagated:
    # fastmcp -> pydocket -> fakeredis -> lupa (optional "lua" extra)
    lupa
  ];

  # No tests in the package build (run separately in CI)
  doCheck = false;

  # Ensure the entry point script is created
  postInstall = ''
    # Verify the entry point exists
    test -x $out/bin/mcp-deadmansnitch
  '';

  meta = {
    description = "MCP server for Dead Man's Snitch monitoring service";
    longDescription = ''
      A Model Context Protocol (MCP) server for Dead Man's Snitch monitoring service.
      This server enables AI assistants like Claude to interact with Dead Man's Snitch
      to monitor scheduled tasks and cron jobs.

      Features:
      - List and search monitoring snitches
      - Check in (ping) snitches to confirm tasks are running
      - Create new monitors for scheduled jobs
      - Update, pause, or delete existing monitors
      - Manage tags for organizing snitches
    '';
    homepage = "https://github.com/jamesbrink/mcp-deadmansnitch";
    repository = "https://github.com/jamesbrink/mcp-deadmansnitch";
    documentation = "https://github.com/jamesbrink/mcp-deadmansnitch#readme";
    license = lib.licenses.mit;
    maintainers = [
      {
        name = "James Brink";
        email = "james@jamesbrink.net";
        github = "jamesbrink";
      }
    ];
    platforms = lib.platforms.unix;
    mainProgram = "mcp-deadmansnitch";
  };
}
