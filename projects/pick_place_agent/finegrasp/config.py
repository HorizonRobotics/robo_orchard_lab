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
from typing import Literal

from pydantic import BaseModel, Field


class TrainerParam(BaseModel):
    lr_scheduler_step_at: Literal["epoch", "step"] = Field(
        default="step",
        description="Frequency of updating the learning rate (in steps)",
    )
    max_step: int = Field(
        default=None, ge=1, description="Maximum number of steps for training"
    )
    max_epoch: int = Field(
        default=None, ge=1, description="Maximum number of epochs for training"
    )
    step_eval_freq: int = Field(
        default=None,
        ge=1,
        description="Frequency of evaluation during training (in steps)",
    )
    epoch_eval_freq: int = Field(
        default=None,
        ge=1,
        description="Frequency of evaluation during training (in epochs)",
    )
    resume_from: str = Field(
        default=None,
        description="Path to the checkpoint for resuming training",
    )
    resume_share_dir: str = Field(
        default=None,
        description="Path to the shared directory for resuming training",
    )
    grad_clip_mode: Literal["norm", "value"] = Field(
        default=None, description="Gradient clipping mode (norm or value)"
    )
    grad_clip_value: float = Field(
        default=None, ge=0.0, description="Maximum value for gradient clipping"
    )
    grad_max_norm: float = Field(
        default=None, ge=0.0, description="Maximum norm for gradient clipping"
    )
    grad_norm_type: int = Field(
        default=2, ge=1, description="Type of norm for gradient clipping"
    )
    train_split: str = Field(
        default="train",
        description="Dataset split to use for training",
    )
    test_split: str = Field(
        default="test",
        description="Dataset split to use for testing",
    )
    data_root: str = Field(
        default=None,
        description="Path to the root directory of the dataset",
    )
    lr: float = Field(
        default=0.008, ge=0.0, description="Learning rate for the optimizer"
    )
    train_batch_size: int = Field(
        default=4, ge=1, description="Batch size for training"
    )
    train_num_workers: int = Field(
        default=16,
        ge=0,
        description="Number of worker threads for data loading during training",  # noqa: E501
    )
    eval_batch_size: int = Field(
        default=16, ge=1, description="Batch size for evaluation"
    )
    eval_num_workers: int = Field(
        default=4,
        ge=0,
        description="Number of worker threads for data loading during evaluation",  # noqa: E501
    )
    test_mode: list = Field(
        default=["test", "test_scale"],
        description="List of test modes to evaluate the model on",
    )
    save_epoch_freq: int = Field(
        default=None,
        ge=1,
        description="Frequency of evaluation during training (in epochs)",
    )
    save_step_freq: int = Field(
        default=None,
        ge=1,
        description="Frequency of saving checkpoints during training",
    )
    step_log_freq: int = Field(
        default=64,
        ge=1,
        description="Frequency of logging during training (in steps)",
    )
    world_size: int = Field(
        default=1,
        ge=1,
        description="Number of processes for distributed training",
    )


class DatasetParam(BaseModel):
    data_root: str = Field(
        ..., description="Path to the root directory of the dataset"
    )
    camera: Literal["realsense", "kinect"] = Field(
        default="realsense", description="Camera type used for capturing data"
    )
    num_sample_points: int = Field(
        default=20000,
        ge=1,
        description="Number of points to sample from the point cloud",
    )
    voxel_size: float = Field(
        default=0.005,
        ge=0.0,
        description="Voxel size used for point cloud voxelization",
    )
    remove_outlier: bool = Field(
        default=True,
        description="Whether to remove outlier points from the point cloud",
    )
    remove_invisible: bool = Field(
        default=True,
        description="Whether to remove invisible points from the dataset",
    )
    augment: bool = Field(
        default=True,
        description="Whether to apply data augmentation during training",
    )
    load_label: bool = Field(
        default=True, description="Whether to load labels for the dataset"
    )
    split: Literal[
        "train", "test", "test_seen", "test_similar", "test_novel"
    ] = Field(
        default="train",
        description="Dataset split to use (train, val, or test)",
    )
    batch_size: int = Field(
        default=16, ge=1, description="Batch size for training or evaluation"
    )
    num_workers: int = Field(
        default=16,
        ge=0,
        description="Number of worker threads for data loading",
    )
    use_new_graspness: bool = Field(
        default=False,
        description="Whether to use the new graspness calculation method",
    )


class OptimizerParam(BaseModel):
    lr: float = Field(
        default=0.00025, ge=0.0, description="Learning rate for the optimizer"
    )
    weight_decay: float = Field(
        default=1e-4,
        ge=0.0,
        description="Weight decay (L2 regularization) factor",
    )
    warmup_epoch: int = Field(
        default=1,
        ge=0,
        description="Number of warmup epochs for learning rate scheduling",
    )


class MetricParam(BaseModel):
    voxel_size_cd: float = Field(
        default=0.005,
        ge=0.0,
        description="Voxel size used for collision detection",
    )
    collision_thresh: float = Field(
        default=0.01,
        ge=-1,
        description="Threshold for collision detection",
    )
    camera: Literal["realsense", "kinect"] = Field(
        default="realsense", description="Camera type used for capturing data"
    )
    test_mode: list = Field(
        default=["test", "test_seen", "test_similar", "test_novel"],
        description="List of test modes to evaluate the model on",
    )
    num_test_proc: int = Field(
        default=16,
        ge=1,
        description="Number of processes to use for testing",
    )
    grasp_max_width: float = Field(
        default=0.1,
        ge=0.0,
        description="Maximum gripper width for grasp generation",
    )
    num_seed_points: int = Field(
        default=4096,
        ge=1,
        description="Maximum number of points sampled from the point cloud",
    )
    data_root: str = Field(
        default=None,
        description="Path to the root directory of the dataset",
    )


def get_trainer_cfg():
    trainer_cfg = TrainerParam(
        max_epoch=10,
        save_epoch_freq=1,
        epoch_eval_freq=100,
        step_log_freq=25,
        data_root="data/graspnet1b",
        train_split="train",
        test_split="test",
        test_mode=["test", "test_scale"],
        lr=0.008,
        train_batch_size=4,
        grad_clip_mode="norm",
        grad_max_norm=10,
        lr_scheduler_step_at="step",
    )
    return trainer_cfg


def build_model():
    from robo_orchard_lab.models.finegrasp import (
        FineGrasp,
        FineGraspConfig,
        losses,
    )

    objectnessloss = losses.ObjectnessLoss(loss_weight=1)
    graspnessloss = losses.GraspnessLoss(loss_weight=10)
    viewloss = losses.ViewLoss(loss_weight=100)
    angleloss = losses.AngleLoss(loss_weight=1)
    depthloss = losses.DepthLoss(loss_weight=1)
    scoreclsloss = losses.ScoreClsLoss(loss_weight=1)
    widthloss = losses.WidthLoss(loss_weight=10)

    loss = [
        objectnessloss,
        graspnessloss,
        viewloss,
        angleloss,
        depthloss,
        scoreclsloss,
        widthloss,
    ]

    model_cfgs = FineGraspConfig(
        model_name="FineGrasp",
        seed_feat_dim=512,
        graspness_threshold=0.1,
        grasp_max_width=0.1,
        num_depth=4,
        num_view=300,
        num_angle=12,
        num_seed_points=1024,
        voxel_size=0.005,
        cylinder_radius=0.07,
        cylinder_groups=[0.25, 0.5, 0.75, 1.0],
        use_normal=False,
        loss=loss,
    )

    model = FineGrasp(cfg=model_cfgs)
    return model_cfgs, model


def build_optimizer(model, trainer_cfg):
    import numpy as np
    import torch.optim as optim

    def linear_warmup_with_cosdecay(
        cur_step, warmup_steps, total_steps, min_scale=1e-5
    ):
        if cur_step < warmup_steps:
            return (1 - min_scale) * cur_step / warmup_steps + min_scale
        else:
            ratio = (cur_step - warmup_steps) / total_steps
            return (1 - min_scale) * 0.5 * (
                1 + np.cos(np.pi * ratio)
            ) + min_scale

    optim_cfgs = OptimizerParam(
        lr=trainer_cfg.lr, weight_decay=1e-5, warmup_epoch=1
    )
    optimizer = optim.Adam(
        model.parameters(),
        lr=optim_cfgs.lr,
        weight_decay=optim_cfgs.weight_decay,
    )

    steps_per_epoch = trainer_cfg.max_step / trainer_cfg.max_epoch
    warmup_step = steps_per_epoch * optim_cfgs.warmup_epoch
    total_step = trainer_cfg.max_step

    lr_scheduler = optim.lr_scheduler.LambdaLR(
        optimizer,
        lr_lambda=lambda x: linear_warmup_with_cosdecay(
            x, warmup_step, total_step
        ),
    )
    return optim_cfgs, optimizer, lr_scheduler


def build_metric(model_cfgs, trainer_cfg, eval_save_dir):
    from robo_orchard_lab.dataset.graspnet1b.metrics import (
        GraspNetMetric,
    )

    metric_cfgs = MetricParam(
        voxel_size_cd=0.01,
        # collision_thresh=0.01,
        collision_thresh=-1,
        camera="realsense",
        test_mode=trainer_cfg.test_mode,
        num_test_proc=30,
        grasp_max_width=model_cfgs.grasp_max_width,
        num_seed_points=model_cfgs.num_seed_points,
        data_root=trainer_cfg.data_root,
    )

    metric = GraspNetMetric(
        voxel_size_cd=metric_cfgs.voxel_size_cd,
        collision_thresh=metric_cfgs.collision_thresh,
        eval_save_dir=eval_save_dir,
        camera=metric_cfgs.camera,
        test_mode=metric_cfgs.test_mode,
        num_test_proc=metric_cfgs.num_test_proc,
        grasp_max_width=metric_cfgs.grasp_max_width,
        num_seed_points=metric_cfgs.num_seed_points,
        data_root=metric_cfgs.data_root,
    )
    return metric_cfgs, metric


def build_dataset(trainer_cfg):
    from torch.utils.data import DataLoader

    from robo_orchard_lab.dataset.collates import collate_batch_dict
    from robo_orchard_lab.dataset.graspnet1b import EconomicGraspNet1BDataset

    base_data_cfgs = DatasetParam(
        data_root=trainer_cfg.data_root,
        camera="realsense",
        num_sample_points=20000,
        voxel_size=0.005,
        remove_outlier=True,
        remove_invisible=True,
        augment=True,
        load_label=True,
        use_new_graspness=True,
        split="train",
        batch_size=4,
        num_workers=4,
    )
    train_data_cfgs = base_data_cfgs.model_copy(
        update={
            "split": trainer_cfg.train_split,
            "batch_size": trainer_cfg.train_batch_size,
            "num_workers": trainer_cfg.train_num_workers,
        }
    )
    val_data_cfgs = base_data_cfgs.model_copy(
        update={
            "split": trainer_cfg.test_split,
            "batch_size": trainer_cfg.eval_batch_size,
            "num_workers": trainer_cfg.eval_num_workers,
            "augment": False,
            "load_label": False,
        }
    )

    train_dataset = EconomicGraspNet1BDataset(data_cfgs=train_data_cfgs)
    val_dataset = EconomicGraspNet1BDataset(data_cfgs=val_data_cfgs)

    train_dataloader = DataLoader(
        train_dataset,
        batch_size=train_data_cfgs.batch_size,
        shuffle=True,
        num_workers=train_data_cfgs.num_workers,
        pin_memory=True,
        collate_fn=collate_batch_dict,
        persistent_workers=(train_data_cfgs.num_workers > 0),
    )

    val_dataloader = DataLoader(
        val_dataset,
        batch_size=val_data_cfgs.batch_size,
        shuffle=False,
        num_workers=val_data_cfgs.num_workers,
        pin_memory=False,
        collate_fn=collate_batch_dict,
        persistent_workers=(val_data_cfgs.num_workers > 0),
    )

    return (
        train_data_cfgs,
        val_data_cfgs,
        train_dataloader,
        val_dataloader,
    )
