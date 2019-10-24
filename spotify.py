from subprocess import Popen, PIPE


def get_current_song():
    process = Popen("bash $HOME/domos/media/sp.sh current", shell=True, stdout=PIPE)
    rc = process.wait()
    info = process.stdout.readline().decode().replace("\n", "").split(" | ")

    # author, song
    return info[0], info[1]


def perform_spotify_action(spotify_command):
    process = Popen("bash $HOME/domos/media/sp.sh " + spotify_command, shell=True,
                    stdout=PIPE)
    rc = process.wait()
    if rc == 1:
        return {"ok": False}
    return {"ok": True}


def playpause():
    return perform_spotify_action("play")


def next_song():
    return perform_spotify_action("next")


def prev_song():
    return perform_spotify_action("prev")


if __name__ == "__main__":
    print(get_current_song())
