from clab_datalogger_receiver.received_structure import (
    DataStruct,
    PlottingStruct,
    StructField,
)


def confront_datastructs(tested: DataStruct, ground_truth: DataStruct) -> bool:
    if not tested.name == ground_truth.name:
        return False

    if not tested.struct_format_string == ground_truth.struct_format_string:
        return False

    for tested_f, ground_truth_f in zip(tested.fields, ground_truth.fields):
        if not tested_f.name == ground_truth_f.name:
            return False
        if not tested_f.data_type == ground_truth_f.data_type:
            return False

    return True


def confront_plotting_struct(
    tested: PlottingStruct, ground_truth: PlottingStruct
):
    for s_t, s_gt in zip(tested.subplots, ground_truth.subplots):
        if not confront_datastructs(s_t, s_gt):
            return False

    return True


def test_from_dict():
    t = DataStruct.from_dict({'a': 'f', 'b': 'd', 'c': 'float'}, name='test')
    t_test = DataStruct(
        [
            StructField(data_type='f', name='a'),
            StructField(data_type='d', name='b'),
            StructField(data_type='f', name='c'),
        ],
        name='test',
    )

    assert confront_datastructs(t, t_test)


def test_from_yaml_single():
    t = PlottingStruct(
        [
            DataStruct(
                name=None,
                fields=[StructField(name='accel_data', data_type='f')],
            )
        ]
    )

    t2 = PlottingStruct.from_yaml_file('tests/test_struct_cfg_single.yaml')

    print(t2.subplots[0])
    print(t2.struct_format_string)
