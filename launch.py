"""PyInstaller entry point: GUI without arguments, diagnostic CLI with arguments."""
import sys

def main():
    if len(sys.argv)>1:
        from ecu_workbench.cli import main as diagnostic_main
        return diagnostic_main()
    from ecu_workbench.gui import start
    start()
    return 0

if __name__=='__main__':
    raise SystemExit(main())
