try:

    if __name__ == "__main__":
        import pygame
        import sys
        from src.config import ConfigLoader, ConfigError
        from koia.menu import Menu

        def main() -> int:
            if len(sys.argv) != 2:
                print(
                    "Usage: python3 pac-man.py <config.json>",
                    file=sys.stderr
                )
                return 1

            try:
                config_loader = ConfigLoader(sys.argv[1])
                config = config_loader.load()

            except ConfigError as error:
                print(f"Config error: {error}", file=sys.stderr)
                return 1

            pygame.init()

            try:
                # Internally the game stays 1000x800, but Pygame scales
                # the window on small laptops or large cluster monitors.
                # RESIZABLE and SCALED also keep mouse input mapped to
                # these original logical coordinates.
                try:
                    flags = pygame.SCALED | pygame.RESIZABLE
                    screen = pygame.display.set_mode((1000, 800), flags)
                except pygame.error:
                    screen = pygame.display.set_mode((1000, 800))
                pygame.display.set_caption("PACMAN - Signature Edition")

                menu = Menu(screen, config)
                menu.activate_menu()

            except KeyboardInterrupt:
                print("Game exited. USER INTERRUPTION")

            finally:
                pygame.quit()

            return 0

        sys.exit(main())

except MemoryError:
    print("Error: not enough memory")
    raise SystemExit(1)

except FileNotFoundError as error:
    print(f"Error: file not found: {error}")
    raise SystemExit(1)

except PermissionError as error:
    print(f"Error: permission denied: {error}")
    raise SystemExit(1)

except ValueError as error:
    print(f"Error: invalid value: {error}")
    raise SystemExit(1)

except TypeError as error:
    print(f"Error: invalid type: {error}")
    raise SystemExit(1)

except ImportError as error:
    print(f"Error: import problem: {error}")
    raise SystemExit(1)

except OSError as error:
    print(f"Error: operating system error: {error}")
    raise SystemExit(1)

except RuntimeError as error:
    print(f"Error: runtime error: {error}")
    raise SystemExit(1)

except Exception as error:
    print(f"Error: {type(error).__name__}: {error}")
    raise SystemExit(1)

except BaseException:
    print("Game exited")
