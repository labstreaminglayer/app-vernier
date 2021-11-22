from subprocess import Popen, PIPE


def test_scan():
    p = Popen(["vernier-lsl", "--scan"], stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    assert (
        "Available devices. Default sensors are marked by *." in out.decode()
    )

