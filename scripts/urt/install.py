import logging
from maya import mel
from maya import cmds


log = logging.getLogger(__name__)
ROOT_PACKAGE = __name__.rsplit(".", 1)[0]

URT_COMMAND = """
from {0}.tools.URT_atulshakya import MainDialog
MainDialog.showDialog()
""".format(ROOT_PACKAGE)

SHELF_NAME = "URT_atulshakya"
SHELF_TOOLS = [
    {
        "label": "urt",
        "command": URT_COMMAND,
        "annotation": "Open URT Toolkit",
        "image1": "urtLogo_orange.png",
        "sourceType": "python"
    }
]


def execute():
    """
    Add a new shelf in Maya with all the tools that are provided in the
    SHELF_TOOLS variable. If the tab exists it will be deleted and re-created
    from scratch.
    """
    shelf_main = mel.eval("$tmpVar=$gShelfTopLevel")
    shelves = cmds.tabLayout(shelf_main, query=True, childArray=True)

    if SHELF_NAME in shelves:
        cmds.deleteUI(SHELF_NAME)

    cmds.shelfLayout(SHELF_NAME, parent=shelf_main)

    for tool in SHELF_TOOLS:
        if tool.get("image1"):
            cmds.shelfButton(style="iconOnly", parent=SHELF_NAME, **tool)
        else:
            cmds.shelfButton(style="textOnly", parent=SHELF_NAME, **tool)

    log.info("urt-toolkit installed successfully.")