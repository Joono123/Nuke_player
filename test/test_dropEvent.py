def __drop_items(self, event: QtGui.QDropEvent):
    """
    ListView내에서 드롭되었을 경우 해당 데이터의 URL(파일 경로)을
    딕셔너리에 저장 후 각 파일의 썸네일을 추출하여 임시 디렉토리에 저장
    모델에서 데이터를 다시 로드하여 UI를 새로 불러옴
    """
    self.__lineEdit_debug.setText("파일 로드 중")
    if event.mimeData().hasUrls():
        event.setDropAction(QtCore.Qt.CopyAction)
        urls = event.mimeData().urls()

        # 1개 이상의 파일이 드롭 되는 경우, idx와 url을 딕셔너리에 저장
        for idx, url in enumerate(urls):
            file_path = url.toLocalFile()
            url_str = url.toString()
            # 드롭한 파일이 비디오 형식이 맞는지 확인
            if not self.__is_file_video(url_str):
                print(f"\033[31mERROR: '{file_path}'는 지원하지 않는 형식입니다.\033[0m")
                return
            else:
                pass
            # 딕셔너리 안에 이미 파일 경로가 존재할 경우
            if file_path in self.__file_data.values():
                print(f"\033[31mERROR: '{file_path}'가 이미 등록되었습니다.\033[0m")
                continue

            # 등록 순으로 idx를 부여하기 위함
            if idx in self.__file_data.keys():
                last_idx = list(self.__file_data.keys())[-1]
                self.__file_data[last_idx + 1] = file_path

            # 최초 등록 시
            else:
                self.__file_data[idx] = file_path
        # 썸네일 추출
        self.__extract_thumbnails()

        # 썸네일 디렉토리의 파일 검색 후 모델 새로고침
        self.__thumb_lst = list(
            map(
                lambda x: x.as_posix(),
                sys_lib.System.get_files_lst(pathlib.Path(self.thumb_dir), ".jpg"),
            )
        )
        self.__file_lst = list(self.__file_data.values())
        self.__itemview_model = NP_model.NP_ItemModel(self.__thumb_lst, self.__file_lst)
        self.__item_listview.setModel(self.__itemview_model)

        # 아이템 선택 시 시그널 발생
        self.__item_listview.selectionModel().selectionChanged.connect(
            self.__slot_selection_item
        )

        self.__lineEdit_debug.setText("파일을 선택하세요")
        event.acceptProposedAction()
    else:
        event.ignore()
