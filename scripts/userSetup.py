from maya import cmds


def main():
    from urt import install
    install.execute()


cmds.evalDeferred(main)