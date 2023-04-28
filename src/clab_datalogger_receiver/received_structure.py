"""Module that contains the data structure to represent the received struct."""

from __future__ import annotations

import os
import struct
import sys
from dataclasses import dataclass
from typing import Dict, List, Type

from yaml import safe_load as load_yaml

from .base.common import resource_path

types_dict = {
    'c': 'c',
    'x': 'x',
    'b': 'b',
    'B': 'B',
    '?': '?',
    'h': 'h',
    'H': 'H',
    'u': 'u',
    'I': 'I',
    'l': 'l',
    'L': 'L',
    'q': 'q',
    'Q': 'Q',
    'n': 'n',
    'N': 'N',
    'f': 'f',
    'd': 'd',
    'NULL': 'x',
    'char': 'c',
    'int8': 'b',
    'uint8': 'B',
    '_Bool': '?',
    'int16': 'h',
    'uint16': 'H',
    'int': 'u',
    'uint': 'I',
    'long': 'l',
    'int32': 'l',
    'ulong': 'L',
    'uint32': 'L',
    'long long': 'q',
    'int64': 'q',
    'unsigned long long': 'Q',
    'uint64': 'Q',
    'ssize_t': 'n',
    'size_t': 'N',
    'float': 'f',
    'double': 'd',
}

template_file_path: str = 'templates/struct_cfg_template.yaml'


@dataclass
class StructField:
    """
    Basic class to keep the type of a single field.

    This can be or not be named.
    """

    data_type: str
    name: str | None = None


@dataclass
class DataStruct:
    """Class that represents a single subplot instance."""

    fields: List[StructField]
    name: str | None = None

    def __getitem__(self, index: int):
        """Return the i-th field."""
        return self.fields[index]

    def __len__(self) -> int:
        """Return the count of `self.fields`."""
        return len(self.fields)

    @classmethod
    def from_dict(
        cls: Type[DataStruct],
        data_dict: Dict[str, str],
        name: str | None = None,
    ):
        """Build the class from a dict of field names and types."""
        for field_type in data_dict.values():
            assert field_type in types_dict, (
                f'Type "{field_type}"' 'not supported'
            )

        fields = [
            StructField(data_type=types_dict[field_type], name=field_name)
            for field_name, field_type in data_dict.items()
        ]

        return cls(fields, name=name)

    @classmethod
    def from_data_string(
        cls: Type[DataStruct],
        data_string: str,
        name: str | None = None,
        names: List[str] | None = None,
    ) -> DataStruct:
        """
        Load the configuration from a field list.

        example:
            ['fff'] load an unnamed struct with three floats
            ['fd'] load an unnamed struct with a float and a double

        """
        fields = []
        name_idx = 0

        for field_type_str in data_string:
            if names is not None:
                name = names[name_idx]
                name_idx += 1
            else:
                name = None

            fields.append(
                StructField(data_type=types_dict[field_type_str], name=name)
            )

        return cls(fields, name=None)

    @property
    def struct_format_string(self) -> str:
        """
        Return the format string representation of this class.

        This format is compliant with the `struct.unwrap` method
        """
        return self.get_struct_format_str()

    def get_struct_format_str(self) -> str:
        """
        Return the format string representation of this class.

        This format is compliant with the `struct.unwrap` method
        """
        return ''.join([types_dict[f.data_type] for f in self.fields])

    @property
    def struct_byte_size(self) -> int:
        """Get the expected byte size of this structure."""
        return self.get_struct_byte_size()

    def get_struct_byte_size(self) -> int:
        """Get the expected byte size of this structure."""
        return struct.calcsize(self.struct_format_string)


class PlottingStruct:
    """
    Structure that represents the overall structure sent by the STM.

    Wraps also utilities methods to ease its management
    """

    subplots: List[DataStruct]

    def __init__(self, subplots: List[DataStruct]) -> None:
        """Init the class."""
        self.subplots = subplots

    @classmethod
    def from_yaml_file(cls, filename='struct_cfg.yaml'):
        """Create class from yamlconfiguration file."""

        file_exists = os.path.isfile(filename)

        if not file_exists:
            subpath = os.path.dirname(sys.argv[0])

            with open(
                resource_path(template_file_path, subpath), 'rb'
            ) as t_file:
                with open(filename, 'wb') as w_file:
                    w_file.write(t_file.read())
            print('File created from template')

        with open(filename, 'rt', encoding='utf-8') as file:
            data_s = load_yaml(file)

        assert len(data_s) > 0, 'No data in file'
        # assert len(data_s) == 1, 'More than one plot is not yet supported'

        datas = []
        for data_i in data_s:
            # print(data_i)
            obj = data_i

            s_name = list(obj.keys())[0]
            s_types = obj[s_name]

            datas.append(DataStruct.from_dict(s_types, name=s_name))
            # print('name=', s_name)
            # print('types=', s_types)

        return cls(datas)

    @classmethod
    def from_string_list(cls, packets_strings: List[str]):
        """
        Build the class from the list of packet spec strings.

        The packets sttrings follows the convention of `struct.unpack`
        """
        return cls(
            [DataStruct.from_data_string(p_s) for p_s in packets_strings]
        )

    def __getitem__(self, index: int):
        """Get the i-th subplot."""
        return self.subplots[index]

    def __len__(self) -> int:
        """Get the subplot list lenght."""
        return len(self.subplots)

    @property
    def struct_format_string(self) -> List[str]:
        """Get the format string list of the child structs."""
        return self.get_struct_str()

    def get_struct_str(self) -> List[str]:
        """Get the format string list of the child structs."""
        return [s.struct_format_string for s in self.subplots]

    @property
    def struct_byte_size(self) -> int:
        """Get the total byte size of the child structs."""
        return self.get_struct_byte_size()

    def get_struct_byte_size(self) -> int:
        """Get the total byte size of the child structs."""
        return sum(s.struct_byte_size for s in self.subplots)


# -----------------------------------------------------------------------------
# Tests
if __name__ == '__main__':
    dic = {'a': 'f', 'b': 'd', 'c': 'float'}

    t = DataStruct.from_dict(dic, name='test')

    print('datastruct from dict')
    print(t.name)
    print([(f.name, f.data_type) for f in t.fields])
    print(t.struct_format_string)

    print()
    print('plotting struct from yaml')
    print()
    t2 = PlottingStruct.from_yaml_file()
    print(t2.subplots[0])
    print(t2.struct_format_string)
