# coding: utf8
# ! /usr/env/python
"""
Created on Tue Feb 27 16:25:11 2018

@author: barnhark
"""
import matplotlib
import numpy as np
import pytest

from landlab import RasterModelGrid
from landlab.components import (
    ChannelProfiler,
    DepressionFinderAndRouter,
    FastscapeEroder,
    FlowAccumulator,
    LinearDiffuser,
)

matplotlib.use("agg")


def test_assertion_error():
    """Test that the correct assertion error will be raised."""
    mg = RasterModelGrid(10, 10)
    z = mg.add_zeros("topographic__elevation", at="node")
    z += 200 + mg.x_of_node + mg.y_of_node + np.random.randn(mg.size("node"))

    mg.set_closed_boundaries_at_grid_edges(
        bottom_is_closed=True,
        left_is_closed=True,
        right_is_closed=True,
        top_is_closed=True,
    )
    mg.set_watershed_boundary_condition_outlet_id(0, z, -9999)
    fa = FlowAccumulator(
        mg, flow_director="D8", depression_finder=DepressionFinderAndRouter
    )
    sp = FastscapeEroder(mg, K_sp=.0001, m_sp=.5, n_sp=1)
    ld = LinearDiffuser(mg, linear_diffusivity=0.0001)

    dt = 100
    for i in range(200):
        fa.run_one_step()
        flooded = np.where(fa.depression_finder.flood_status == 3)[0]
        sp.run_one_step(dt=dt, flooded_nodes=flooded)
        ld.run_one_step(dt=dt)
        mg.at_node["topographic__elevation"][0] -= 0.001  # Uplift

    with pytest.raises(ValueError):
        ChannelProfiler(mg, starting_nodes=[0], number_of_watersheds=2)


def test_asking_for_too_many_watersheds():
    mg = RasterModelGrid(10, 10)
    z = mg.add_zeros("topographic__elevation", at="node")
    z += 200 + mg.x_of_node + mg.y_of_node
    mg.set_closed_boundaries_at_grid_edges(
        bottom_is_closed=True,
        left_is_closed=True,
        right_is_closed=True,
        top_is_closed=True,
    )
    mg.set_watershed_boundary_condition_outlet_id(0, z, -9999)
    fa = FlowAccumulator(mg, flow_director="D8")
    sp = FastscapeEroder(mg, K_sp=.0001, m_sp=.5, n_sp=1)

    dt = 100
    for i in range(200):
        fa.run_one_step()
        sp.run_one_step(dt=dt)
        mg.at_node["topographic__elevation"][0] -= 0.001

    with pytest.raises(ValueError):
        ChannelProfiler(mg, number_of_watersheds=3)


def test_no_threshold():
    mg = RasterModelGrid(10, 10)
    z = mg.add_zeros("topographic__elevation", at="node")
    z += 200 + mg.x_of_node + mg.y_of_node + np.random.randn(mg.size("node"))

    mg.set_closed_boundaries_at_grid_edges(
        bottom_is_closed=True,
        left_is_closed=True,
        right_is_closed=True,
        top_is_closed=True,
    )
    mg.set_watershed_boundary_condition_outlet_id(0, z, -9999)
    fa = FlowAccumulator(
        mg, flow_director="D8", depression_finder=DepressionFinderAndRouter
    )
    fa.run_one_step()

    profiler = ChannelProfiler(mg)

    assert profiler.threshold == 2.0


def test_no_drainage_area():
    mg = RasterModelGrid(10, 10)
    mg.add_zeros("topographic__elevation", at="node")
    mg.add_zeros('drainage_area', at='node')
    mg.add_zeros("flow__link_to_receiver_node", at="node")
    mg.add_zeros("flow__receiver_node", at="node")
    with pytest.raises(ValueError):
        ChannelProfiler(mg)


def test_no_flow__link_to_receiver_node():
    mg = RasterModelGrid(10, 10)
    mg.add_zeros("topographic__elevation", at="node")
    mg.add_zeros("drainage_area", at="node")
    mg.add_zeros('flow__link_to_receiver_node', at='node')
    mg.add_zeros("flow__receiver_node", at="node")
    with pytest.raises(ValueError):
        ChannelProfiler(mg)


def test_no_flow__receiver_node():
    mg = RasterModelGrid(10, 10)
    mg.add_zeros("topographic__elevation", at="node")
    mg.add_zeros("drainage_area", at="node")
    mg.add_zeros("flow__link_to_receiver_node", at="node")
    mg.add_zeros('flow__receiver_node', at='node')
    with pytest.raises(ValueError):
        ChannelProfiler(mg)


def test_plotting():
    mg = RasterModelGrid(40, 60)
    z = mg.add_zeros("topographic__elevation", at="node")
    z += 200 + mg.x_of_node + mg.y_of_node
    mg.set_closed_boundaries_at_grid_edges(
        bottom_is_closed=True,
        left_is_closed=True,
        right_is_closed=True,
        top_is_closed=True,
    )
    mg.set_watershed_boundary_condition_outlet_id(0, z, -9999)
    fa = FlowAccumulator(mg, flow_director="D8")
    sp = FastscapeEroder(mg, K_sp=.0001, m_sp=.5, n_sp=1)

    dt = 100
    for i in range(200):
        fa.run_one_step()
        sp.run_one_step(dt=dt)
        mg.at_node["topographic__elevation"][0] -= 0.001

    profiler = ChannelProfiler(mg, number_of_watersheds=1)
    profiler.run_one_step()

    profiler.plot_profiles()
    profiler.plot_profiles_in_map_view()