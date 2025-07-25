# Project RoboOrchard
#
# Copyright (c) 2024-2025 Horizon Robotics. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.
import os
import random
import string
from typing import Generator

import datasets as hg_datasets
import pytest
import torch
from sqlalchemy import select
from sqlalchemy.orm import Session

from robo_orchard_lab.dataset.datatypes import (
    BatchJointsState,
    BatchJointsStateFeature,
)
from robo_orchard_lab.dataset.robot.dataset import RODataset, ROMultiRowDataset
from robo_orchard_lab.dataset.robot.db_orm import (
    Episode,
    Instruction,
    Robot,
    Task,
)
from robo_orchard_lab.dataset.robot.packaging import (
    DataFrame,
    DatasetPackaging,
    EpisodeData,
    EpisodeMeta,
    EpisodePackaging,
    InstructionData,
    RobotData,
    TaskData,
)
from robo_orchard_lab.dataset.robot.row_sampler import (
    DeltaTimestampSamplerConfig,
)


class DummyEpisodePackaging(EpisodePackaging):
    def __init__(
        self,
        gen_frame_num: int,
        data_size: int = 16,
        robots: list[RobotData] | None = None,
        tasks: list[TaskData] | None = None,
        instructions: list[InstructionData] | None = None,
    ):
        self._gen_frame_num = gen_frame_num
        self._candidate_robots = robots or []
        self._candidate_tasks = tasks or []
        self._candidate_instructions = instructions or []
        self._data_size = data_size

    def gen_robot(self) -> RobotData | None:
        if len(self._candidate_robots) == 0:
            return None
        return random.choice(self._candidate_robots)

    def gen_task(self) -> TaskData | None:
        if len(self._candidate_tasks) == 0:
            return None
        return random.choice(self._candidate_tasks)

    def gen_instruction(self) -> InstructionData | None:
        if len(self._candidate_instructions) == 0:
            return None
        return random.choice(self._candidate_instructions)

    def generate_episode_meta(self) -> EpisodeMeta:
        return EpisodeMeta(
            episode=EpisodeData(),
            robot=self.gen_robot(),
            task=self.gen_task(),
        )

    @property
    def features(self) -> hg_datasets.Features:
        return hg_datasets.Features(
            {
                "data": hg_datasets.Value("string"),
                "joints": BatchJointsStateFeature(),
            }
        )

    def generate_frames(self) -> Generator[DataFrame, None, None]:
        for _ in range(self._gen_frame_num):
            instruction = self.gen_instruction()
            yield DataFrame(
                features={
                    "data": "".join(
                        random.choices(
                            string.ascii_lowercase, k=self._data_size
                        )
                    ),
                    "joints": BatchJointsState(
                        position=torch.rand(size=(3, 5)),
                        # velocity=random.rand(7),
                    ),
                },
                instruction=instruction,
            )


@pytest.fixture(scope="module")
def example_dataset_path_no_shard(tmp_local_folder: str) -> str:
    dataset_dir = os.path.join(
        tmp_local_folder,
        "example_dataset_path_"
        + "".join(random.choices(string.ascii_lowercase, k=8)),
    )
    robots = [
        RobotData(name="robot_0", urdf_content="robot_0_urdf"),
        RobotData(name="robot_1", urdf_content="robot_1_urdf"),
    ]
    tasks = [
        TaskData(name="task_0", description="task_0_description"),
        TaskData(name="task_1", description="task_1_description"),
    ]
    instructions = [
        InstructionData(
            name="instruction_0",
            json_content={
                "instruction": "Do task 0 with robot 0",
                "robot": "robot_0",
                "task": "task_0",
            },
        ),
        InstructionData(
            name="instruction_1",
            json_content={
                "instruction": "Do task 1 with robot 1",
                "robot": "robot_1",
                "task": "task_1",
            },
        ),
    ]
    episodes = [
        DummyEpisodePackaging(
            gen_frame_num=5,
            robots=robots[0:1],
            tasks=tasks[0:1],
            instructions=instructions[0:1],
        ),
        DummyEpisodePackaging(gen_frame_num=3, tasks=tasks[1:2]),
    ]
    features = episodes[0].features
    dataset_packaging = DatasetPackaging(
        features=features, database_driver="duckdb"
    )
    dataset_packaging.packaging(episodes=episodes, dataset_path=dataset_dir)
    return dataset_dir


@pytest.fixture(scope="module")
def example_dataset_path_shard(tmp_local_folder: str) -> str:
    dataset_dir = os.path.join(
        tmp_local_folder,
        "example_dataset_path_"
        + "".join(random.choices(string.ascii_lowercase, k=8)),
    )
    robots = [
        RobotData(name="robot_0", urdf_content="robot_0_urdf"),
        RobotData(name="robot_1", urdf_content="robot_1_urdf"),
    ]
    tasks = [
        TaskData(name="task_0", description="task_0_description"),
        TaskData(name="task_1", description="task_1_description"),
    ]
    instructions = [
        InstructionData(
            name="instruction_0",
            json_content={
                "instruction": "Do task 0 with robot 0",
                "robot": "robot_0",
                "task": "task_0",
            },
        ),
        InstructionData(
            name="instruction_1",
            json_content={
                "instruction": "Do task 1 with robot 1",
                "robot": "robot_1",
                "task": "task_1",
            },
        ),
    ]
    episodes = [
        DummyEpisodePackaging(
            gen_frame_num=5,
            robots=robots[0:1],
            tasks=tasks[0:1],
            data_size=1024 * 1024 * 1,
            instructions=instructions[0:1],
        ),
        DummyEpisodePackaging(
            gen_frame_num=3, tasks=tasks[1:2], data_size=1024 * 1024 * 1
        ),
    ]
    features = episodes[0].features
    dataset_packaging = DatasetPackaging(
        features=features, database_driver="duckdb"
    )
    dataset_packaging.packaging(
        episodes=episodes, dataset_path=dataset_dir, max_shard_size="1MB"
    )
    return dataset_dir


@pytest.fixture(
    params=[
        "example_dataset_path_no_shard",
        "example_dataset_path_shard",
    ],
    ids=["no_shard", "shard"],
)
def example_dataset_path(request) -> str:
    """Provide a database engine from different backends."""
    return request.getfixturevalue(request.param)


class TestDatasetPackaging:
    @pytest.fixture
    def example_robots(self) -> list[RobotData]:
        return [
            RobotData(name="robot_0", urdf_content="robot_0_urdf"),
            RobotData(name="robot_1", urdf_content="robot_1_urdf"),
        ]

    @pytest.fixture
    def example_tasks(self) -> list[TaskData]:
        return [
            TaskData(name="task_0", description="task_0_description"),
            TaskData(name="task_1", description="task_1_description"),
        ]

    @pytest.fixture
    def example_instructions(self) -> list[InstructionData]:
        return [
            InstructionData(
                name="instruction_0",
                json_content={
                    "instruction": "Do task 0 with robot 0",
                    "robot": "robot_0",
                    "task": "task_0",
                },
            ),
            InstructionData(
                name="instruction_1",
                json_content={
                    "instruction": "Do task 1 with robot 1",
                    "robot": "robot_1",
                    "task": "task_1",
                },
            ),
        ]

    def test_episode_packaging(
        self,
        tmp_local_folder: str,
        example_robots: list[RobotData],
        example_tasks: list[TaskData],
        example_instructions: list[InstructionData],
    ):
        dataset_dir = os.path.join(
            tmp_local_folder,
            "test_episode_packaging"
            + "".join(random.choices(string.ascii_lowercase, k=8)),
        )
        episodes = [
            DummyEpisodePackaging(
                gen_frame_num=5,
                robots=example_robots[0:1],
                tasks=example_tasks[0:1],
                instructions=example_instructions[0:1],
            ),
            DummyEpisodePackaging(
                gen_frame_num=3,
                tasks=example_tasks[0:1],
            ),
        ]
        features = episodes[0].features
        dataset_packaging = DatasetPackaging(
            features=features, database_driver="sqlite"
        )
        dataset_packaging.packaging(
            episodes=episodes,
            dataset_path=dataset_dir,
        )


class TestDataset:
    def test_load_dataset(self, example_dataset_path: str):
        dataset = RODataset(dataset_path=example_dataset_path)
        assert len(dataset.frame_dataset) == 8
        assert len(dataset.frame_dataset) == len(dataset)
        assert "data" in dataset.frame_dataset.column_names
        assert dataset.db_engine is not None
        assert dataset.dataset_format_version is not None
        print("dataset_format_version: ", dataset.dataset_format_version)

    def test_check_db_engine(self, example_dataset_path: str):
        dataset = RODataset(dataset_path=example_dataset_path)
        assert dataset.db_engine is not None
        with Session(dataset.db_engine) as session:
            # list all episodes by ascending order of id
            total_frame_num = 0
            for episode in session.scalars(
                select(Episode).order_by(Episode.index)
            ).all():
                print("episode:", episode)
                assert episode.frame_num is not None
                assert episode.dataset_begin_index == total_frame_num
                total_frame_num += episode.frame_num

    def test_check_frame_db(self, example_dataset_path: str):
        dataset = RODataset(dataset_path=example_dataset_path)
        last_index = -1
        assert dataset.get_meta(Episode, -1) is None
        print(dataset.frame_dataset.features)
        max_episode_idx = -1
        for frame in dataset.frame_dataset:
            assert isinstance(frame, dict)
            assert frame["index"] > last_index
            last_index = frame["index"]
            episode = dataset.get_meta(Episode, frame["episode_index"])
            assert episode is not None
            assert not isinstance(episode, list)
            assert episode.index == frame["episode_index"]
            max_episode_idx = max(max_episode_idx, episode.index)
            assert frame["index"] >= episode.dataset_begin_index
            assert (
                frame["index"]
                < episode.dataset_begin_index + episode.frame_num
            )
            if frame["robot_index"] is not None:
                robot = dataset.get_meta(Robot, frame["robot_index"])
                assert robot is not None
                assert robot.index == frame["robot_index"]
            if frame["task_index"] is not None:
                task = dataset.get_meta(Task, frame["task_index"])
                assert task
                assert task.index == frame["task_index"]
            if frame["instruction_index"] is not None:
                instruction = dataset.get_meta(
                    Instruction, frame["instruction_index"]
                )
                assert instruction
                assert instruction.index == frame["instruction_index"]

        assert max_episode_idx > 0

    @pytest.mark.parametrize(
        "idx",
        [None, 0, [0, 1], [None, 0]],
    )
    def test_get_meta(
        self, example_dataset_path: str, idx: int | None | list[int | None]
    ):
        dataset = RODataset(dataset_path=example_dataset_path)
        ret = dataset.get_meta(Episode, idx)
        if idx is None:
            assert ret is None
        elif isinstance(idx, list):
            assert isinstance(ret, list)
            for i, single_ret in zip(idx, ret, strict=True):
                if i is None:
                    assert single_ret is None
                else:
                    assert isinstance(single_ret, Episode)
                    assert single_ret.index == i
        else:
            assert isinstance(ret, Episode)
            assert ret.index == idx

    @pytest.mark.parametrize("index2meta", [True, False])
    def test_get_item_by_slice(
        self, example_dataset_path: str, index2meta: bool
    ):
        dataset = RODataset(
            dataset_path=example_dataset_path, meta_index2meta=index2meta
        )
        # test access by slice
        multi_row = dataset[0:2]
        assert isinstance(multi_row, dict)
        if index2meta:
            assert isinstance(multi_row["episode"], list)
            assert isinstance(multi_row["episode"][0], Episode)
        else:
            assert isinstance(multi_row["episode_index"], list)
            assert isinstance(multi_row["episode_index"][0], int)

    @pytest.mark.parametrize("index2meta", [True, False])
    def test_get_item_by_list(
        self, example_dataset_path: str, index2meta: bool
    ):
        dataset = RODataset(
            dataset_path=example_dataset_path, meta_index2meta=index2meta
        )
        # test access by list
        multi_row = dataset[[0, 1, 2]]
        assert isinstance(multi_row, dict)
        if index2meta:
            assert isinstance(multi_row["episode"], list)
            assert isinstance(multi_row["episode"][0], Episode)
        else:
            assert isinstance(multi_row["episode_index"], list)
            assert isinstance(multi_row["episode_index"][0], int)

        multi_row = dataset[[0]]
        assert isinstance(multi_row, dict)
        if index2meta:
            assert isinstance(multi_row["episode"], list)
            assert isinstance(multi_row["episode"][0], Episode)
        else:
            assert isinstance(multi_row["episode_index"], list)
            assert isinstance(multi_row["episode_index"][0], int)

    @pytest.mark.parametrize("index2meta", [True, False])
    def test_get_item_by_int(
        self, example_dataset_path: str, index2meta: bool
    ):
        dataset = RODataset(
            dataset_path=example_dataset_path, meta_index2meta=index2meta
        )
        # test single row access
        row = dataset[0]
        assert isinstance(row, dict)
        if index2meta:
            assert isinstance(row["episode"], Episode)
        else:
            assert isinstance(row["episode_index"], int)

    @pytest.mark.parametrize("index2meta", [True, False])
    def test_get_item_by_str(
        self, example_dataset_path: str, index2meta: bool
    ):
        dataset = RODataset(
            dataset_path=example_dataset_path, meta_index2meta=index2meta
        )
        # test single row access
        row = dataset["joints"]
        assert isinstance(row, hg_datasets.arrow_dataset.Column)
        row = dataset["episode_index"]
        if index2meta:
            assert isinstance(row, list)
            assert isinstance(row[0], Episode)
        else:
            assert isinstance(row, hg_datasets.arrow_dataset.Column)
            assert isinstance(row[0], int)

    @pytest.mark.parametrize("index2meta", [True, False])
    def test_select_columns(self, example_dataset_path: str, index2meta: bool):
        dataset = RODataset(
            dataset_path=example_dataset_path, meta_index2meta=index2meta
        )
        # test select columns
        selected_dataset = dataset.select_columns(["joints"])
        assert isinstance(selected_dataset, RODataset)
        assert "joints" in selected_dataset.features
        print("selected dataset features: ", selected_dataset.features)
        assert len(selected_dataset.features) == 1
        print(selected_dataset[0])
        assert dataset[0]["joints"] == selected_dataset[0]["joints"]

    @pytest.mark.parametrize("index2meta", [True, False])
    def test_select(self, example_dataset_path: str, index2meta: bool):
        dataset = RODataset(
            dataset_path=example_dataset_path, meta_index2meta=index2meta
        )
        offset = 3
        selected_dataset = dataset.select(indices=range(offset, offset + 2))
        assert isinstance(selected_dataset, RODataset)
        assert len(selected_dataset) == 2
        assert selected_dataset[0]["index"] == dataset[offset]["index"]

    @pytest.mark.parametrize("index2meta", [True, False])
    def test_pickleable(self, example_dataset_path: str, index2meta: bool):
        dataset = RODataset(
            dataset_path=example_dataset_path, meta_index2meta=index2meta
        )
        # test pickling
        import pickle

        pickled_dataset = pickle.dumps(dataset)
        print("len(pickled_dataset): ", len(pickled_dataset))
        unpickled_dataset = pickle.loads(pickled_dataset)
        assert isinstance(unpickled_dataset, RODataset)
        assert len(unpickled_dataset) == len(dataset)
        assert unpickled_dataset[0]["joints"] == dataset[0]["joints"]

    @pytest.mark.parametrize("index2meta", [True, False])
    def test_save(
        self,
        example_dataset_path: str,
        tmp_local_folder: str,
        index2meta: bool,
    ):
        dataset = RODataset(
            dataset_path=example_dataset_path, meta_index2meta=index2meta
        )
        new_dataset_dir = os.path.join(
            tmp_local_folder,
            "test_save_"
            + "".join(random.choices(string.ascii_lowercase, k=8)),
        )
        dataset.save_to_disk(dataset_path=new_dataset_dir)
        new_dataset = RODataset(
            dataset_path=new_dataset_dir, meta_index2meta=index2meta
        )
        assert len(new_dataset) == len(dataset)
        assert new_dataset[0]["joints"] == dataset[0]["joints"]


class TestRoboTwinDataset:
    def test_load_train(self, ROBO_ORCHARD_TEST_WORKSPACE: str):
        path = os.path.join(
            ROBO_ORCHARD_TEST_WORKSPACE,
            "robo_orchard_workspace/datasets/robotwin/ro_dataset",
        )
        dataset = RODataset(dataset_path=path, meta_index2meta=True)
        print(len(dataset))
        print(dataset.frame_dataset.features)
        row = dataset[500]
        print(row.keys())
        print("episode: ", row["episode"])
        print("left_camera timestamps: ", row["left_camera"].timestamps)
        print("joints timestamps: ", row["joints"].timestamps)
        print(
            "row timestamp range: ",
            row["timestamp_min"],
            row["timestamp_max"],
        )
        print("left_camera intrinsic: ", row["left_camera"].intrinsic_matrices)


class TestMultiRowDataset:
    def test_empty_delta_ts(self, ROBO_ORCHARD_TEST_WORKSPACE: str):
        path = os.path.join(
            ROBO_ORCHARD_TEST_WORKSPACE,
            "robo_orchard_workspace/datasets/robotwin/ro_dataset",
        )

        dataset = ROMultiRowDataset(
            dataset_path=path,
            row_sampler=DeltaTimestampSamplerConfig(column_delta_ts={}),
        )
        print(len(dataset))
        row = dataset[0]
        print("row keys: ", row.keys())
        for k in row.keys():
            assert not isinstance(row[k], list), (
                f"Expected {k} to not be a list, but got {type(row[k])}"
            )

    def test_with_delta_ts(self, ROBO_ORCHARD_TEST_WORKSPACE: str):
        path = os.path.join(
            ROBO_ORCHARD_TEST_WORKSPACE,
            "robo_orchard_workspace/datasets/robotwin/ro_dataset",
        )

        dataset = ROMultiRowDataset(
            dataset_path=path,
            row_sampler=DeltaTimestampSamplerConfig(
                column_delta_ts={
                    "joints": [0, 0.0 + 0.1],
                },
                tolerance=0.019,
            ),
        )
        row = dataset[0]
        list_column_names = ["joints"]
        for k in row.keys():
            if k in list_column_names:
                assert isinstance(row[k], list), (
                    f"Expected {k} to be a list, but got {type(row[k])}"
                )
            else:
                assert not isinstance(row[k], list), (
                    f"Expected {k} to not be a list, but got {type(row[k])}"
                )

    def test_with_delta_ts_by_slice(self, ROBO_ORCHARD_TEST_WORKSPACE: str):
        path = os.path.join(
            ROBO_ORCHARD_TEST_WORKSPACE,
            "robo_orchard_workspace/datasets/robotwin/ro_dataset",
        )

        dataset = ROMultiRowDataset(
            dataset_path=path,
            row_sampler=DeltaTimestampSamplerConfig(
                column_delta_ts={
                    "joints": [0, 0.0 + 0.1],
                },
                tolerance=0.019,
            ),
        )
        row = dataset[0:3]
        list_column_names = ["joints"]
        for k in row.keys():
            assert isinstance(row[k], list), (
                f"Expected {k} to be a list, but got {type(row[k])}"
            )
            assert len(row[k]) == 3
            if k in list_column_names:
                assert isinstance(row[k][0], list), (
                    f"Expected {k}[0] to be a list, but got {type(row[k])}"
                )
            else:
                assert not isinstance(row[k][0], list), (
                    f"Expected {k} to not be a list, but got {type(row[k])}"
                )

    def test_with_delta_ts_by_list(self, ROBO_ORCHARD_TEST_WORKSPACE: str):
        path = os.path.join(
            ROBO_ORCHARD_TEST_WORKSPACE,
            "robo_orchard_workspace/datasets/robotwin/ro_dataset",
        )

        dataset = ROMultiRowDataset(
            dataset_path=path,
            row_sampler=DeltaTimestampSamplerConfig(
                column_delta_ts={
                    "joints": [0, 0.0 + 0.1],
                },
                tolerance=0.019,
            ),
        )
        row = dataset[[0, 3, 1]]
        list_column_names = ["joints"]
        for k in row.keys():
            assert isinstance(row[k], list), (
                f"Expected {k} to be a list, but got {type(row[k])}"
            )
            assert len(row[k]) == 3
            if k in list_column_names:
                assert isinstance(row[k][0], list), (
                    f"Expected {k}[0] to be a list, but got {type(row[k])}"
                )
            else:
                assert not isinstance(row[k][0], list), (
                    f"Expected {k} to not be a list, but got {type(row[k])}"
                )

    def test_from_dataset(self, ROBO_ORCHARD_TEST_WORKSPACE: str):
        path = os.path.join(
            ROBO_ORCHARD_TEST_WORKSPACE,
            "robo_orchard_workspace/datasets/robotwin/ro_dataset",
        )

        dataset = ROMultiRowDataset.from_dataset(
            RODataset(dataset_path=path),
            row_sampler=DeltaTimestampSamplerConfig(
                column_delta_ts={
                    "joints": [0, 0.0 + 0.1],
                },
                tolerance=0.019,
            ),
        )
        row = dataset[0]
        list_column_names = ["joints"]
        for k in row.keys():
            if k in list_column_names:
                assert isinstance(row[k], list), (
                    f"Expected {k} to be a list, but got {type(row[k])}"
                )
            else:
                assert not isinstance(row[k], list), (
                    f"Expected {k} to not be a list, but got {type(row[k])}"
                )
