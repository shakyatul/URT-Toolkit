from maya import cmds


def main():
    from URT_atulshakya import MainDialog
    MainDialog.showDialog()


cmds.evalDeferred(main)
