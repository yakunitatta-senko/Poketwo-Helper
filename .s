import os
import glob

def delete_all_images(folder_path: str):
    """Delete all image files in the given folder quickly and safely."""
    # Supported image extensions
    extensions = ("*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.bmp", "*.tiff")

    deleted, failed = 0, 0

    for ext in extensions:
        for file_path in glob.iglob(os.path.join(folder_path, ext)):
            try:
                os.remove(file_path)
                deleted += 1
            except Exception as e:
                failed += 1
                print(f"❌ Failed to delete {file_path}: {e}")

    print(f"✅ Deleted {deleted} images, {failed} failed.")

# Example usage:
delete_all_images("/workspaces/Poketwo-Helper/data/commands/pokemon/pokemon_emojis")
