import os
import typing
import json
import typing
import logging
import pathlib

from PySide2 import QtWidgets, QtGui, QtCore


class QtLibs:
    @staticmethod
    def input_dialog(title: str, label: str, parent=None):
        text, ok = QtWidgets.QInputDialog.getText(
            parent,
            title,
            label,
            QtWidgets.QLineEdit.Normal,
            QtCore.QDir().home().dirName(),
        )
        return ok, text

    @staticmethod
    def file_dialog(default_path: str, parent=None) -> typing.Union[pathlib.Path, None]:
        """
        :param default_path:
        :param parent:
        :return:
        """
        dia = QtWidgets.QFileDialog.getOpenFileName(parent=parent, dir=default_path)
        if len(dia):
            return pathlib.Path(dia)
        return None

    @staticmethod
    def dir_dialog(default_path: str, parent=None) -> typing.Union[pathlib.Path, None]:
        """
        :param default_path:
        :param parent:
        :return:
        """
        dia = QtWidgets.QFileDialog.getExistingDirectory(
            parent=parent, dir=default_path
        )
        if len(dia):
            return pathlib.Path(dia)
        return None

    @staticmethod
    def center_on_screen(inst):
        res = QtWidgets.QDesktopWidget().screenGeometry()
        inst.move(
            (res.width() / 2) - (inst.frameSize().width() / 2),
            (res.height() / 2) - (inst.frameSize().height() / 2),
        )

    @staticmethod
    def question_dialog(title: str, text: str, parent=None) -> bool:
        btn: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.question(
            parent, title, text
        )
        return btn == QtWidgets.QMessageBox.StandardButton.Yes

    @staticmethod
    def error_dialog(title: str, text: str, parent=None) -> bool:
        btn: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.warning(
            parent, title, text
        )
        return btn == QtWidgets.QMessageBox.StandardButton.Close

    @staticmethod
    def critical_dialog(title: str, text: str, parent=None) -> bool:
        btn: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.critical(
            parent, title, text
        )
        return btn == QtWidgets.QMessageBox.StandardButton.Close

    @staticmethod
    def info_dialog(title: str, text: str, parent=None) -> bool:
        btn: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.information(
            parent, title, text
        )
        return btn == QtWidgets.QMessageBox.StandardButton.Close


class UISettings:
    KEY_WIN_GEO = "win_geo"
    KEY_WIN_STE = "win_ste"

    def __init__(
        self, window: typing.Any, ini_fpath: pathlib.Path, cfg_fpath: pathlib.Path
    ):
        self.__window = window
        self.__setting_ini = QtCore.QSettings(
            ini_fpath.as_posix(), QtCore.QSettings.IniFormat
        )
        self.__setting_cfg: pathlib.Path = cfg_fpath

    def save_main_window_geometry(self):
        self.__setting_ini.setValue(
            UISettings.KEY_WIN_GEO, self.__window.saveGeometry()
        )
        self.__setting_ini.setValue(UISettings.KEY_WIN_STE, self.__window.saveState())

    def save_cfg_file(self, data):
        with self.__setting_cfg.open("w") as fp:
            json.dump(data, fp)

    def load_main_window_geometry(self):
        main_window_geo = self.__setting_ini.value(UISettings.KEY_WIN_GEO)
        main_window_ste = self.__setting_ini.value(UISettings.KEY_WIN_STE)
        if main_window_geo:
            self.__window.restoreGeometry(main_window_geo)
        else:
            QtLibs.center_on_screen(self.__window)
        if main_window_ste:
            self.__window.restoreState(main_window_ste)

    def load_cfg_dict_from_file(self) -> typing.Dict:
        if not self.__setting_cfg.exists():
            return {}
        with self.__setting_cfg.open("r") as fp:
            try:
                data = json.load(fp)
                return data
            except ValueError as err:
                os.remove(self.__setting_cfg.as_posix())
                return {}


class LogHandler(logging.Handler):
    def __init__(self, out_stream=None):
        super().__init__()
        # log text msg format
        self.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s] : %(message)s")
        )
        logging.getLogger().addHandler(self)
        # logging level
        logging.getLogger().setLevel(logging.DEBUG)
        self.__out_stream = out_stream

    def emit(self, record) -> None:
        msg = self.format(record)
        self.__out_stream.append(msg)
        self.__out_stream.moveCursor(QtGui.QTextCursor.End)

    @classmethod
    def log_msg(cls, method=None, msg: str = "") -> None:
        if method is None:
            return
        if method.__name__ == "info":
            new_msg = "<font color=#dddddd>{msg}</font>".format(msg=msg)
        elif method.__name__ == "debug":
            new_msg = "<font color=#23bcde>{msg}</font>".format(msg=msg)
        elif method.__name__ == "warning":
            new_msg = "<font color=#cc9900>{msg}</font>".format(msg=msg)
        elif method.__name__ == "error":
            new_msg = "<font color=#e32474>{msg}</font>".format(msg=msg)
        elif method.__name__ == "critical":
            new_msg = "<font color=#ff0000>{msg}</font>".format(msg=msg)
        else:
            raise TypeError("[log method] unknown type")
        method(new_msg)


if __name__ == "__main__":
    pass
