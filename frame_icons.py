import os
from PIL import Image


# ============================================================
# CONFIGURATION
# ============================================================

VINTAGE_STORY = os.environ.get("VINTAGE_STORY")

if not VINTAGE_STORY:
    print("ERROR: VINTAGE_STORY environment variable is not set.")
    input("Press Enter to exit...")
    raise SystemExit

ICON_ROOT = os.path.join(VINTAGE_STORY, "icons")

if not os.path.isdir(ICON_ROOT):
    print(f"ERROR: Icons folder not found:")
    print(ICON_ROOT)
    print(f"Please assign your VINTAGE_STORY Environment Variable (as you would for developing VS mods) and then run this program again.")
    input("Press Enter to exit...")
    raise SystemExit

TARGET_SIZE = 64

SUPPORTED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".gif"
}


# ============================================================
# FRAME
# ============================================================

def find_frame():
    """
    Look for frame.png or frame.jpg in the same folder
    as this Python script.
    """

    script_folder = os.path.dirname(os.path.abspath(__file__))

    png = os.path.join(script_folder, "frame.png")
    jpg = os.path.join(script_folder, "frame.jpg")

    if os.path.isfile(png):
        return png

    if os.path.isfile(jpg):
        return jpg

    return None


# ============================================================
# FOLDERS
# ============================================================

def find_icon_folders():
    """
    Find all folders directly inside ICON_ROOT.

    Folders ending with '_framed' are ignored.
    """

    folders = []

    if not os.path.isdir(ICON_ROOT):
        return folders

    for name in os.listdir(ICON_ROOT):

        path = os.path.join(ICON_ROOT, name)

        if not os.path.isdir(path):
            continue

        if name.lower().endswith("_framed"):
            continue

        folders.append(path)

    folders.sort(key=lambda p: os.path.basename(p).lower())

    return folders


# ============================================================
# IMAGE DISCOVERY
# ============================================================

def get_images(folder):
    """Find supported image files directly inside a folder."""

    images = []

    for filename in os.listdir(folder):

        path = os.path.join(folder, filename)

        if not os.path.isfile(path):
            continue

        extension = os.path.splitext(filename)[1].lower()

        if extension in SUPPORTED_EXTENSIONS:
            images.append(path)

    return sorted(images, key=lambda p: os.path.basename(p).lower())


# ============================================================
# IMAGE LOADING / RESIZING
# ============================================================

def load_and_resize(path):

    image = Image.open(path)

    # RGBA is important because your icons are transparent.
    image = image.convert("RGBA")

    image = image.resize(
        (TARGET_SIZE, TARGET_SIZE),
        Image.Resampling.LANCZOS
    )

    return image


# ============================================================
# FOLDER SELECTION
# ============================================================

def choose_folder(folders):
    """
    Interactive Windows console folder selector.

    Arrow Up / Down = navigate
    Enter           = select
    Escape          = cancel
    """

    import msvcrt
    import ctypes

    # Windows console functions
    kernel32 = ctypes.windll.kernel32

    # ------------------------------------------------------------
    # Get console handle
    # ------------------------------------------------------------

    STD_OUTPUT_HANDLE = -11
    handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

    # ------------------------------------------------------------
    # Windows COORD structure
    # ------------------------------------------------------------

    class COORD(ctypes.Structure):
        _fields_ = [
            ("X", ctypes.c_short),
            ("Y", ctypes.c_short)
        ]

    # ------------------------------------------------------------
    # Get current cursor position
    # ------------------------------------------------------------

    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
        _fields_ = [
            ("dwSize", COORD),
            ("dwCursorPosition", COORD),
            ("wAttributes", ctypes.c_ushort),
            ("srWindow", ctypes.c_short * 4),
            ("dwMaximumWindowSize", COORD)
        ]

    info = CONSOLE_SCREEN_BUFFER_INFO()

    kernel32.GetConsoleScreenBufferInfo(
        handle,
        ctypes.byref(info)
    )

    start_x = info.dwCursorPosition.X
    start_y = info.dwCursorPosition.Y

    # ------------------------------------------------------------
    # Folder information
    # ------------------------------------------------------------

    folder_info = []

    for folder in folders:

        name = os.path.basename(folder)
        image_count = len(get_images(folder))

        folder_info.append(
            (folder, name, image_count)
        )

    selected = 0

    # ------------------------------------------------------------
    # Draw menu
    # ------------------------------------------------------------

    def move_cursor(x, y):
        position = COORD(x, y)

        kernel32.SetConsoleCursorPosition(
            handle,
            position
        )

    def draw_menu():

        move_cursor(start_x, start_y)

        for index, (folder, name, image_count) in enumerate(folder_info):

            if index == selected:
                line = f"> {name} ({image_count} images)"
            else:
                line = f"  {name} ({image_count} images)"

            # Clear the entire line before printing.
            print(
                line.ljust(100),
                end=""
            )

            # Move to next line.
            print()

        print()
        print("↑/↓ Navigate    Enter Select    Esc Cancel".ljust(100))

    # ------------------------------------------------------------
    # Initial draw
    # ------------------------------------------------------------

    print()
    print("Available icon folders:")
    print("----------------------------------------")

    menu_start_y = start_y + 2

    start_y = menu_start_y

    draw_menu()

    # ------------------------------------------------------------
    # Input loop
    # ------------------------------------------------------------

    while True:

        key = msvcrt.getwch()

        # --------------------------------------------------------
        # Arrow keys
        # --------------------------------------------------------

        if key in ("\x00", "\xe0"):

            key = msvcrt.getwch()

            # Up arrow
            if key == "H":

                selected -= 1

                if selected < 0:
                    selected = len(folder_info) - 1

                draw_menu()

            # Down arrow
            elif key == "P":

                selected += 1

                if selected >= len(folder_info):
                    selected = 0

                draw_menu()

        # --------------------------------------------------------
        # Enter
        # --------------------------------------------------------

        elif key == "\r":

            # Move below the menu before continuing.
            move_cursor(
                start_x,
                start_y + len(folder_info) + 3
            )

            return folder_info[selected][0]

        # --------------------------------------------------------
        # Escape
        # --------------------------------------------------------

        elif key == "\x1b":

            move_cursor(
                start_x,
                start_y + len(folder_info) + 3
            )

            print("Cancelled.")

            return None
    """
    Interactive Windows console folder selector.

    Arrow Up / Down = navigate
    Enter           = select
    Escape          = cancel
    """

    import msvcrt

    # Pre-calculate image counts
    folder_info = []

    for folder in folders:
        name = os.path.basename(folder)
        image_count = len(get_images(folder))
        folder_info.append((folder, name, image_count))

    selected = 0

    def draw_menu():
        # Move cursor to the beginning of the menu.
        # After the first draw, this overwrites the previous menu.
        if draw_menu.first_draw:
            print()
            print("Available icon folders:")
            print("----------------------------------------")
            draw_menu.first_draw = False
        else:
            # Move cursor up by number of folder lines.
            print(f"\033[{len(folder_info)}A", end="")

        for index, (folder, name, image_count) in enumerate(folder_info):

            if index == selected:
                print(
                    f"\033[2K> {name} ({image_count} images)"
                )
            else:
                print(
                    f"\033[2K  {name} ({image_count} images)"
                )

        print()
        print("↑/↓ Navigate    Enter Select    Esc Cancel")

    draw_menu.first_draw = True

    draw_menu()

    while True:

        key = msvcrt.getwch()

        # --------------------------------------------------------
        # Arrow keys
        # --------------------------------------------------------

        if key in ("\x00", "\xe0"):

            key = msvcrt.getwch()

            # Up arrow
            if key == "H":

                selected -= 1

                if selected < 0:
                    selected = len(folder_info) - 1

                draw_menu()

            # Down arrow
            elif key == "P":

                selected += 1

                if selected >= len(folder_info):
                    selected = 0

                draw_menu()

        # --------------------------------------------------------
        # Enter
        # --------------------------------------------------------

        elif key == "\r":

            # Clear the menu area a little before continuing.
            print()

            return folder_info[selected][0]

        # --------------------------------------------------------
        # Escape
        # --------------------------------------------------------

        elif key == "\x1b":

            print()
            print("Cancelled.")

            return None

    print()
    print("Available icon folders:")
    print("----------------------------------------")

    for index, folder in enumerate(folders, start=1):

        name = os.path.basename(folder)

        images = get_images(folder)

        print(f"{index}. {name} ({len(images)} images)")

    print("----------------------------------------")
    print()

    while True:

        choice = input(
            f"Choose a folder (1-{len(folders)}): "
        ).strip()

        try:
            number = int(choice)

        except ValueError:
            print("Please enter a number.")
            continue

        if 1 <= number <= len(folders):
            return folders[number - 1]

        print("Invalid selection.")


# ============================================================
# PROCESS
# ============================================================

def process_icons(frame_path, icon_folder):

    print()
    print("Loading frame...")

    try:
        frame = load_and_resize(frame_path)

    except Exception as e:
        print(f"ERROR: Could not load frame.")
        print(e)
        return

    icons = get_images(icon_folder)

    print()
    print(f"Found {len(icons)} icon(s).")
    print()

    if len(icons) == 0:
        print("No supported images were found.")
        return

    # --------------------------------------------------------
    # Confirmation
    # --------------------------------------------------------

    while True:

        answer = input(
            "Start processing these icons? (Y/n): "
        ).strip().lower()

        # Empty input = Yes
        if answer == "" or answer == "y":
            break

        if answer == "n":
            print("Cancelled.")
            return

        print("Please enter Y or N.")

    # --------------------------------------------------------
    # Output folder
    # --------------------------------------------------------

    folder_name = os.path.basename(
        os.path.normpath(icon_folder)
    )

    parent_folder = os.path.dirname(
        os.path.normpath(icon_folder)
    )

    output_folder = os.path.join(
        parent_folder,
        folder_name + "_framed"
    )

    os.makedirs(output_folder, exist_ok=True)

    print()
    print("Output folder:")
    print(output_folder)
    print()

    # --------------------------------------------------------
    # Process icons
    # --------------------------------------------------------

    successful = 0
    failed = 0

    for icon_path in icons:

        icon_name = os.path.basename(icon_path)

        print(f"Processing icon {icon_name}...")

        try:

            icon = load_and_resize(icon_path)

            # Make a fresh frame for this icon.
            result = frame.copy()

            # Since both are 64x64, this places the icon
            # exactly in the center.
            result.alpha_composite(
                icon,
                (0, 0)
            )

            # Always output PNG to preserve transparency.
            base_name = os.path.splitext(icon_name)[0]

            output_path = os.path.join(
                output_folder,
                base_name + ".png"
            )

            result.save(
                output_path,
                "PNG"
            )

            successful += 1

        except Exception as e:

            print(
                f"  ERROR processing {icon_name}: {e}"
            )

            failed += 1

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("========================================")
    print("Finished!")
    print("========================================")
    print(f"Successfully processed: {successful}")
    print(f"Failed:                 {failed}")
    print()
    print("Output folder:")
    print(output_folder)
    print("========================================")
    print()

    while True:

        answer = input(
            "Open output folder? (Y/n): "
        ).strip().lower()

        # Empty input = Yes
        if answer == "" or answer == "y":

            # Open the folder in Windows Explorer
            os.startfile(output_folder)

            # Exit immediately.
            # The BAT won't pause afterwards.
            raise SystemExit

        if answer == "n":
            break

        print("Please enter Y or N.")


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Find frame
    # --------------------------------------------------------

    frame_path = find_frame()

    if frame_path is None:

        print(
            "No frame.png or frame.jpg was found "
            "in the program folder."
        )

        print()

        frame_path = input(
            "Paste the full path to your frame image: "
        ).strip().strip('"')

        if not os.path.isfile(frame_path):

            print()
            print("ERROR: Frame does not exist.")
            print(frame_path)
            return

    else:

        print("Found frame:")
        print(frame_path)

    # --------------------------------------------------------
    # Find folders
    # --------------------------------------------------------

    print()
    print("Icon root:")
    print(ICON_ROOT)

    folders = find_icon_folders()

    if len(folders) == 0:

        print()
        print("No icon folders were found.")
        return

    # --------------------------------------------------------
    # Choose folder
    # --------------------------------------------------------

    selected_folder = choose_folder(folders)

    if selected_folder is None:
        return

    print()
    print("Selected folder:")
    print(selected_folder)

    process_icons(
        frame_path,
        selected_folder
    )


if __name__ == "__main__":
    main()