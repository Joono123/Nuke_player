#!/usr/bin/env python
# -*- coding: utf-8 -*-

# author        : Seongcheol Jeon
# created date  : 2024.02.15
# modified date : 2024.02.15
# description   :

import typing


class _SingletonWrapper:
    def __init__(self, cls):
        self.__wrapped = cls
        self.__instance = None

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            self.__instance = self.__wrapped(*args, **kwargs)
        return self.__instance


def singleton(cls):
    return _SingletonWrapper(cls)


class BitMask:
    def __init__(self):
        self.__field = 0b0000

    # def __str__(self) -> str:
    #     bits = list()
    #     digits = 8
    #     for i in range(digits):
    #         bits.append(str((self.__INSTANCE.FIELD >> (digits - 1 - i)) & 0x01))
    #         if ((i + 1) % 4) == 0:
    #             bits.append(' ')
    #     return ''.join(bits)

    def get_show_field(self):
        bits = list()
        digits = 8
        for i in range(digits):
            bits.append(str((self.__field >> (digits - 1 - i)) & 0x01))
            if ((i + 1) % 4) == 0:
                bits.append(' ')
        return ''.join(bits)

    @property
    def field(self):
        return self.__field

    def __activate(self, num: int) -> None:
        self.__field |= (0x01 << num)

    def __deactivate(self, num: int) -> None:
        self.__field &= (~(0x01 << num))

    def __toggle(self, num: int) -> None:
        self.__field ^= (0x01 << num)

    def __confirm(self, num: int) -> bool:
        return bool(self.__field & (0x01 << num))

    def activate(self, bitfield: int) -> None:
        self.__field |= bitfield

    def deactivate(self, bitfield: int) -> None:
        self.__field &= (~bitfield)

    def toggle(self, bitfield: int) -> None:
        self.__field ^= bitfield

    def confirm(self, bitfield: int) -> bool:
        return bool(self.__field & bitfield)

    def confirm_onebit(self, num: int) -> bool:
        return bool(self.__field & (0x01 << num))

    def empty(self) -> None:
        self.__field = 0

    def all(self) -> None:
        self.__field = -1


@singleton
class SingletonBitMask(BitMask): ...


class Stack:
    class Node:
        def __init__(self, data):
            self.data = data
            self.next = None

    def __init__(self):
        self.top = None

    def push(self, data) -> None:
        if self.top is None:
            self.top = Stack.Node(data)
        else:
            node = Stack.Node(data)
            node.next = self.top
            self.top = node

    def pop(self) -> typing.Any:
        if self.top is None:
            return None
        node = self.top
        self.top = self.top.next
        return node.data

    def peek(self) -> typing.Any:
        if self.top is None:
            return None
        return self.top.data

    def is_empty(self) -> bool:
        return self.top is None


if __name__ == '__main__':
    pass
