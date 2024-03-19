def __slot_del_file(self):
    if not len(self.__play_lst):
        self.__lineEdit_debug.setText("ERROR: 삭제할 파일이 선택되지 않았습니다")
    for f_path in self.__play_lst:
        thumbs = os.path.splitext(os.path.basename(f_path))[0] + ".jpg"
        thumbs_path = os.path.join(self.thumb_dir, thumbs)
        if os.path.exists(thumbs_path):
            os.remove(thumbs_path)
            self.__thumb_lst.remove(thumbs_path)
            self.delete_key_from_value(self.__file_data, f_path)
            self.__file_lst.remove(f_path)
            self.__play_lst.remove(f_path)
        else:
            self.__lineEdit_debug.setText("ERROR: 삭제할 파일이 존재하지 않습니다")

        # 파일 리스트 재정의 및 모델 갱신
        print("-" * 100)
        print(
            f"thumb_list: {self.__thumb_lst}\nfile_lst: {self.__file_lst}\nfile_data: {self.__file_data}"
        )
        self.__itemview_model = NP_model.NP_ItemModel(self.__thumb_lst, self.__file_lst)
        self.__item_listview.setModel(self.__itemview_model)
        self.__listview_model = NP_model.NP_ListModel(self.__play_lst)
        self.__text_listview.setModel(self.__listview_model)
        self.__item_listview.selectionModel().selectionChanged.connect(
            self.__slot_icon_idxs
        )
