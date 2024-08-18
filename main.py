import os
import shutil
import subprocess


def list_filenames(directory: str) -> list[str]:
    try:
        # Get the list of all files and directories in the specified directory
        files_and_dirs: list[str] = os.listdir(directory)

        # Filter the list to include only files
        filenames = [f for f in files_and_dirs if is_video_file(directory, f)]

        return filenames
    except FileNotFoundError:
        return f"The directory '{directory}' does not exist."
    except Exception as e:
        return f"An error occurred: {e}"


def is_video_file(directory: str, filename: str) -> bool:
    return os.path.isfile(os.path.join(directory, filename)) and filename.upper().endswith('.MP4')


def clear_processed_dir(processed_media_dir: str):
    for filename in os.listdir(processed_media_dir):
        file_path = os.path.join(processed_media_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Remove the file or symbolic link
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Remove the directory and its contents
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')


def copy_files_to_processed(media_dir: str, dest_dir: str, filenames: list[str]):
    for filename in filenames:
        src = os.path.join(media_dir, filename)
        dest = os.path.join(dest_dir, filename)
        print(f"Copying {src} to {dest}...")
        shutil.copy(src, dest)


def group_related_videos(video_filenames: list[str]) -> dict[str, list[str]]:
    grouped = {}
    for filename in video_filenames:
        group_name = filename[:8]

        grouped_filenames: list[str] = None
        if (group_name in grouped):
            grouped_filenames: list[str] = grouped[group_name]
        else:
            grouped_filenames: list[str] = []
            grouped[group_name] = grouped_filenames

        grouped_filenames.append(filename)
        grouped_filenames.sort()

    return grouped


def create_input_parameter_file(processed_dir: str, filenames: list[str]):
    with open(os.path.join(processed_dir, "filelist.txt"), 'w') as file:
        for filename in filenames:
            line = "file '{fname}'\n".format(fname=filename)
            file.write(line)


def join_videofile(processed_dir: str, output_filename: str):
    command = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', os.path.join(processed_dir, "filelist.txt"),
        '-c', 'copy',
        os.path.join(processed_dir, output_filename + '.MP4')
    ]
    try:
        # Run the command
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Print the output
        print("Command output:", result.stdout.decode())
        print("Command error:", result.stderr.decode())

    except subprocess.CalledProcessError as e:
        # Handle errors in running the command
        print(f"Error running command: {e}")
        print("Command output:", e.stdout.decode())
        print("Command error:", e.stderr.decode())


def delete_input_files(processed_dir: str, input_files: list[str]):
    for filename in input_files:
        os.remove(os.path.join(processed_dir, filename))


media_dir = '/media/benedict/disk/DCIM/100MEDIA'
processed_media_dir = './processed'

clear_processed_dir(processed_media_dir)
video_filenames = list_filenames(media_dir)
copy_files_to_processed(media_dir, processed_media_dir, video_filenames)

video_filenames = list_filenames(processed_media_dir)
grouped_filenames = group_related_videos(video_filenames)

for filename in grouped_filenames:
    create_input_parameter_file(processed_media_dir, grouped_filenames[filename])
    join_videofile(processed_media_dir, filename)
    delete_input_files(processed_media_dir, grouped_filenames[filename])
