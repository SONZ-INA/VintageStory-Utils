import os
from PIL import Image
from InquirerPy import inquirer


# ============================================================
# CONFIGURATION
# ============================================================

VINTAGE_STORY = os.environ.get("VINTAGE_STORY")

if not VINTAGE_STORY:
    print("ERROR: VINTAGE_STORY environment variable is not set.")
    input("Press Enter to exit...")
    exit()

ICON_ROOT = os.path.join(VINTAGE_STORY, "icons")

if not os.path.isdir(ICON_ROOT):
    print("ERROR: Icons folder not found:")
    print(ICON_ROOT)
    input("Press Enter to exit...")
    exit()

TARGET_SIZE = 64

SUPPORTED_EXTENSIONS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".gif",
)

DIRECTIONAL_SUFFIXES = (
    "-east",
    "-west",
    "-north",
    "-south",
)


# ============================================================
# FRAME
# ============================================================

def find_frame():
    script_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    possible_frames = [
        os.path.join(script_dir, "frame.png"),
        os.path.join(script_dir, "frame.jpg"),
    ]

    for path in possible_frames:
        if os.path.isfile(path):
            return path

    print(
        "Could not find frame.png or frame.jpg "
        "next to the script."
    )

    frame_path = input(
        "Enter path to frame image: "
    ).strip('"')

    if not os.path.isfile(frame_path):
        print("ERROR: Frame file not found.")
        input("Press Enter to exit...")
        exit()

    return frame_path


# ============================================================
# ICON FOLDERS
# ============================================================

def find_icon_folders():
    folders = []

    for name in os.listdir(ICON_ROOT):
        path = os.path.join(ICON_ROOT, name)

        if (
            os.path.isdir(path)
            and not name.lower().endswith("_framed")
        ):
            folders.append(path)

    return sorted(folders, key=lambda p: os.path.basename(p).lower())


def get_images(folder_path):
    images = []

    for name in os.listdir(folder_path):
        path = os.path.join(
            folder_path,
            name
        )

        if not os.path.isfile(path):
            continue

        if not name.lower().endswith(
            SUPPORTED_EXTENSIONS
        ):
            continue

        images.append(path)

    images.sort(
        key=lambda p:
        os.path.basename(p).lower()
    )

    return images
    folder_path = os.path.join(
        ICON_ROOT,
        folder
    )

    images = []

    for name in os.listdir(folder_path):
        path = os.path.join(
            folder_path,
            name
        )

        if not os.path.isfile(path):
            continue

        if not name.lower().endswith(
            SUPPORTED_EXTENSIONS
        ):
            continue

        images.append(path)

    images.sort(
        key=lambda p:
        os.path.basename(p).lower()
    )

    return images


# ============================================================
# IMAGE GROUPING
# ============================================================

def get_group_name(image_path):
    """
    Removes one directional suffix from an icon name.

    Example:

        coolingcabinet-east.png
        coolingcabinet-west.png
        coolingcabinet-north.png
        coolingcabinet-south.png

    Become:

        coolingcabinet
    """

    filename = os.path.basename(
        image_path
    )

    stem, _ = os.path.splitext(
        filename
    )

    stem_lower = stem.lower()

    for suffix in DIRECTIONAL_SUFFIXES:
        if stem_lower.endswith(suffix):
            return stem[:-len(suffix)]

    return stem


def group_images(images):
    groups = {}

    for image in images:
        group_name = get_group_name(
            image
        )

        if group_name not in groups:
            groups[group_name] = []

        groups[group_name].append(
            image
        )

    for group in groups:
        groups[group].sort(
            key=lambda p:
            os.path.basename(p).lower()
        )

    return dict(
        sorted(
            groups.items(),
            key=lambda item:
            item[0].lower()
        )
    )


# ============================================================
# IMAGE FILTERING
# ============================================================

def filter_images(
    images,
    filter_mode
):
    if filter_mode == "everything":
        return images

    if filter_mode == "single":
        return images

    if filter_mode == "east":
        result = []

        for image in images:
            filename = os.path.splitext(
                os.path.basename(image)
            )[0].lower()

            if (
                filename.endswith("-west")
                or filename.endswith("-north")
                or filename.endswith("-south")
            ):
                continue

            result.append(image)

        return result

    return images


# ============================================================
# RESIZE
# ============================================================

def load_and_resize(path):
    """Load an image, convert to RGBA, and resize to 64x64."""
    image = Image.open(path).convert("RGBA")
    return image.resize((TARGET_SIZE, TARGET_SIZE), Image.Resampling.LANCZOS)


# ============================================================
# FOLDER SELECTION
# ============================================================

def choose_folder(folders):
    choices = [
        os.path.basename(folder)
        for folder in folders
    ]

    selected = inquirer.select(
        message="Available icon folders:",
        choices=choices,
        pointer="❯",
        instruction="Use ↑/↓ to select, Enter to confirm, Esc to quit",
        qmark=""
    ).execute()

    if selected is None:
        return None

    for folder in folders:
        if os.path.basename(folder) == selected:
            return folder

    return None


# ============================================================
# FILTER SELECTION
# ============================================================

def choose_filter():
    choices = [
        "East only",
        "Everything",
        "Single",
    ]

    selected = inquirer.select(
        message="Filter icons:",
        choices=choices,
        pointer="❯",
        instruction=(
            "Use ↑/↓ to select, "
            "Enter to confirm, "
            "Esc to go back"
        ),
        qmark=""
    ).execute()

    if selected == "East only":
        return "east"

    if selected == "Everything":
        return "everything"

    if selected == "Single":
        return "single"

    return None


# ============================================================
# SINGLE GROUP SELECTION
# ============================================================

def choose_single_group(images):
    groups = group_images(
        images
    )

    if not groups:
        print(
            "No icons found."
        )

        return None

    choices = []

    for group_name, variants in groups.items():
        variant_count = len(
            variants
        )

        variant_word = (
            "variant"
            if variant_count == 1
            else "variants"
        )

        choices.append(
            (
                f"{group_name} "
                f"({variant_count} {variant_word})"
            )
        )

    selected = inquirer.select(
        message="Select icon:",
        choices=choices,
        pointer="❯",
        max_height="70%",
        instruction=(
            "Use ↑/↓ to navigate, "
            "Enter to confirm, "
            "Esc to go back"
        ),
        qmark=""
    ).execute()

    if selected is None:
        return None

    # Find which group corresponds to the
    # selected display string.
    for group_name, variants in groups.items():
        variant_count = len(
            variants
        )

        variant_word = (
            "variant"
            if variant_count == 1
            else "variants"
        )

        display_name = (
            f"{group_name} "
            f"({variant_count} {variant_word})"
        )

        if display_name == selected:
            return variants

    return None


# ============================================================
# SINGLE VARIANT SELECTION
# ============================================================

def choose_single_variant(images):
    if not images:
        return None

    # No reason to show a menu if there is
    # only one possible variant.
    if len(images) == 1:
        return images[0]

    choices = [
        os.path.basename(image)
        for image in images
    ]

    selected = inquirer.select(
        message="Select variant:",
        choices=choices,
        pointer="❯",
        instruction=(
            "Use ↑/↓ to navigate, "
            "Enter to confirm, "
            "Esc to go back"
        ),
        qmark=""
    ).execute()

    if selected is None:
        return None

    for image in images:
        if os.path.basename(
            image
        ) == selected:
            return image

    return None


# ============================================================
# PROCESS ICONS
# ============================================================

def process_icons(frame_path, icon_folder, filter_mode, selected_icon=None):
    # --------------------------------------------------------
    # Load and resize the frame
    # --------------------------------------------------------
    frame = load_and_resize(frame_path)

    if selected_icon:
        images = [selected_icon]
    else:
        images = filter_images(get_images(icon_folder), filter_mode)

    print()
    print(f"Filter: {filter_mode}")
    print(f"Found {len(images)} icon(s).")

    if not images:
        print("Nothing to process.")
        return

    if not selected_icon:
        confirm = inquirer.select(
            message="Start processing these icons?",
            choices=[
                "Yes",
                "No / Go back"
            ],
            pointer="❯",
            instruction=(
                "Use ↑/↓ to select, "
                "Enter to confirm, "
                "Esc to go back"
            ),
            qmark=""
        ).execute()

        if confirm is None or confirm == "No / Go back":
            print("Going back...")
            return

    output_folder = os.path.join(
        os.path.dirname(icon_folder),
        os.path.basename(icon_folder) + "_framed"
    )
    
    os.makedirs(output_folder, exist_ok=True)

    print()
    print(f"Output: {output_folder}")
    print()

    processed = 0

    for icon_path in images:
        try:
            # ------------------------------------------------
            # Load and resize the icon to 64x64
            # ------------------------------------------------
            icon = load_and_resize(icon_path)

            # ------------------------------------------------
            # Create a fresh 64x64 image
            # ------------------------------------------------
            output = Image.new(
                "RGBA",
                (TARGET_SIZE, TARGET_SIZE),
                (0, 0, 0, 0)
            )

            # ------------------------------------------------
            # Frame goes FIRST
            # ------------------------------------------------
            output.alpha_composite(frame, (0, 0))

            # ------------------------------------------------
            # Icon goes ON TOP, centered
            # Since both are 64x64, this is simply 0,0.
            # ------------------------------------------------
            output.alpha_composite(icon, (0, 0))

            # ------------------------------------------------
            # Save
            # ------------------------------------------------
            output_path = os.path.join(
                output_folder,
                os.path.splitext(os.path.basename(icon_path))[0] + ".png"
            )

            output.save(output_path)
            processed += 1

            print(f"  ✓ {os.path.basename(icon_path)}")

        except Exception as e:
            print(f"  ✗ {os.path.basename(icon_path)}: {e}")

    print()
    print(f"Processed {processed}/{len(images)} icon(s).")

    if processed > 0:
        open_output = inquirer.confirm(
            message="Open output folder?",
            default=True
        ).execute()

        if open_output:
            os.startfile(output_folder)


# ============================================================
# MAIN
# ============================================================

def main():
    frame_path = find_frame()

    folders = find_icon_folders()

    if not folders:
        print(
            "No icon folders found in:"
        )

        print(
            ICON_ROOT
        )

        input(
            "Press Enter to exit..."
        )

        return

    while True:
        selected_folder = choose_folder(
            folders
        )

        if selected_folder is None:
            print()
            print(
                "Exiting."
            )

            return

        while True:
            filter_mode = choose_filter()

            if filter_mode is None:
                print()
                print(
                    "Going back to folder selection..."
                )

                break

            # =================================================
            # SINGLE
            # =================================================

            if filter_mode == "single":
                all_icons = get_images(
                    selected_folder
                )

                if not all_icons:
                    print()
                    print(
                        "No icons found in this folder."
                    )

                    input(
                        "Press Enter to continue..."
                    )

                    continue

                # Select the icon group.
                selected_group = (
                    choose_single_group(
                        all_icons
                    )
                )

                if selected_group is None:
                    print()
                    print(
                        "Going back to filter selection..."
                    )

                    continue

                # Select a directional variant.
                selected_icon = (
                    choose_single_variant(
                        selected_group
                    )
                )

                if selected_icon is None:
                    print()
                    print(
                        "Going back to icon selection..."
                    )

                    continue

                # Process immediately.
                process_icons(
                    frame_path,
                    selected_folder,
                    filter_mode,
                    selected_icon
                )

                return

            # =================================================
            # EAST / EVERYTHING
            # =================================================

            process_icons(
                frame_path,
                selected_folder,
                filter_mode
            )

            return


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()