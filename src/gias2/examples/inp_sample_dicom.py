#!/usr/bin/env python
"""
FILE: inp_sample_dicom.py
LAST MODIFIED: 19/03/18
DESCRIPTION:
Sample a DICOM stack at the element centroids of an INP mesh. From the sampled
HU, calculate Young's modulus based on power law.

===============================================================================
This file is part of GIAS2. (https://bitbucket.org/jangle/gias2)

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
===============================================================================
"""

import os
import sys
import argparse

os.environ['ETS_TOOLKIT'] = 'qt4'

import numpy as np
from gias2.visualisation import fieldvi
from gias2.image_analysis.image_tools import Scan
from gias2.mesh import simplemesh
from gias2.mesh import vtktools, inp, tetgenoutput

E_BINS = np.linspace(0.1, 1e5, 10)[:-1]
E_BIN_VALUES = E_BINS

parser = argparse.ArgumentParser(
    description='Sample a DICOM stack at the element centroids of an INP mesh.'
    )
parser.add_argument(
    'inp',
    help='INP file'
    )
parser.add_argument(
    'dicomdir',
    help='directory containing dicom stack'
    )
parser.add_argument(
    'output',
    help='output INP file'
    )
parser.add_argument(
    '--dicompat',
    default='\.dcm',
    help='file pattern of dicom files'
    )
parser.add_argument(
    '-e', '--elset',
    default=None,
    help='The ELSET in the INP file to fit. If not given, the first ELSET will be used.'
    )
parser.add_argument(
    '--flipz',
    action='store_true',
    help='Flip the Z (axial) axis of the dicom stack'
    )
parser.add_argument(
    '-v', '--view',
    action='store_true',
    help='view results in mayavi'
    )

#=============================================================================#
def _load_inp(fname, meshname=None):
    """
    Reads mesh meshname from INP file. If meshname not defined, reads the 1st mesh.

    Returns a inp.Mesh instance.
    """
    reader = inp.InpReader(fname)
    header = reader.readHeader()
    if meshname is None:
        meshname = reader.readMeshNames()[0]

    return reader.readMesh(meshname), header

def calc_elem_centroids(mesh):
    node_mapping = dict(zip(mesh.nodeNumbers, mesh.nodes))
    elem_shape = np.array(mesh.elems).shape
    elem_nodes_flat = np.hstack(mesh.elems)
    elem_node_coords_flat = np.array([node_mapping[i] for i in elem_nodes_flat])
    elem_node_coords = elem_node_coords_flat.reshape([elem_shape[0], elem_shape[1], 3])
    elem_centroids = elem_node_coords.mean(1)
    return elem_centroids

def bin_correct(x, bins, bin_values):
    """
    Given a list of scalars x, sort them into bins defined by "ranges", then
    replace their values by the value of each bin defined in "bin_values".

    inputs:
    -------
    x: 1D array of scalars
    bins: a sequence of bin left edges.
    bin_values: a sequence of values of length equal to the number of bins.
        Values to reassign to each x depending on its bin.

    returns:
    --------
    x_binned: 1D array of values after binning and value reassignment.
    bins: the indices of x grouped by bins
    """

    if len(bins)!=len(bin_values):
        raise ValueError('bins and bin_values must have same length')

    if x.min()<min(bins):
        raise ValueError("lowest bin edge must be smaller or equal to x.min()")

    bin_inds = np.digitize(x, bins=bins, right=False)
    x_binned = np.zeros_like(x)
    bins = []
    for bi, bv in enumerate(bin_values):
        bin_i_inds = np.where(bin_inds==bi+1)[0]
        x_binned[bin_i_inds] = bv
        bins.append(bin_i_inds)

    return x_binned, bins

PHANTOM_HU = (19.960/(19.960 + 17.599))*1088 + (17.599/(17.599 + 19.960))*1055
WATER_HU = -2
UPPER_E = 16700 # in MPa. From Jacob Munro's material properties document.
RHO_PHANTOM = 800 # mg mm3^-1
RHO_OTHER_MAT = 0.626*(2000000/2017.3)**(1/2.46)

def powerlaw(hu):
    """
    Calculate youngs modulus from HU using power law
    """

    # Fix very low density values to a 2MPa value
    rho_HA = (hu - WATER_HU)*RHO_PHANTOM/(PHANTOM_HU - WATER_HU)
    rho_HA[rho_HA < RHO_OTHER_MAT] = RHO_OTHER_MAT
    rho_app = rho_HA/0.626

    Young = 2017.3*(rho_app**2.46)/1000000 # factor of 1000000 is to convert pascals into megapascals

    return Young

#=============================================================================#
# parse inputs
args = parser.parse_args()

inp_filename = args.inp #'data/tibia_volume.inp'
dicomdir = args.dicomdir #'data/tibia_surface.stl'
output_filename = args.output #'data/tibia_morphed.stl'

# import volumetric mesh
inp_mesh, inp_header = _load_inp(inp_filename, args.elset)
vol_nodes = inp_mesh.getNodes()
vol_nodes = np.array(vol_nodes)

# load dicom
s = Scan('scan')
s.loadDicomFolder(
    dicomdir, filter=False, filePattern=args.dicompat, newLoadMethod=True
    )
if args.flipz:
    s.I = s.I[:,:,::-1]

# calculate element centroids
centroids = inp_mesh.calcElemCentroids()
centroids_img = s.coord2Index(centroids, zShift=True, negSpacing=False, roundInt=False)

# sample image at element centroids - use quadratic interpolation
# inp_points = target_tet.volElemCentroids
# target_points_5 = s.coord2Index(target_tet.volElemCentroids)
# target_points_5[:, 2] = -target_points_5[:, 2]
sampled_hu = s.sampleImage(
    centroids_img, maptoindices=0, outputType=float, order=2,
    )

# Convert HU to Young's Modulus
E = powerlaw(sampled_hu)

# bin and correct E
E_binned, E_bin_inds  = bin_correct(E, E_BINS, E_BIN_VALUES)


# create a new INP "mesh" for each bin
# binned_meshes = []
# for bi, bin_inds in enumerate(E_bin_inds):
#     m = inp.Mesh('BONE{:03d}'.format(bi+1))
#     m.setElems()
#======================================================================#
# # write out INP file
# mesh = inp_mesh
# writer = inp.InpWriter(outputFilename)
# writer.addMesh(mesh)
# writer.write()

# # write out per-element material property
# f = open(outputFilename, 'a')

# # write start of section
# f.write('** extra\n')
# line1_pattern = '*Elset, elset=ST{}\n'
# line2_pattern = ' {}\n'
# cnt=0

# for ei, e_number in enumerate(inp_mesh.elemNumbers):
#     cnt += 1
#     line1 = line1_pattern.format(cnt)
#     line2 = line2_pattern.format(e_number)
#     f.write(line1)
#     f.write(line2)
    
# line1_pattern = '**Section: Section-{}\n'
# line2_pattern = '*Solid Section, elset=ST{}, material=MT{}\n'
# cnt2=0

# for ei, e_number in enumerate(mesh.elemNumbers):
#     cnt2 += 1
#     line1 = line1_pattern.format(cnt2)
#     line2 = line2_pattern.format(cnt2,cnt2)
#     f.write(line1)
#     f.write(line2)
    
# # Right now, bright bone of the phantom on the DICOM has average HU value of 1073 HU and water on the DICOM has average HU value of -2



# line1_pattern = '*Material, name=MT{}\n'
# line2_pattern = '*Elastic\n'
# line3_pattern = ' {}, {}\n'

# cnt3=0

# for ei, e_number in enumerate(mesh.elemNumbers):
#     cnt3 += 1
#     line1 = line1_pattern.format(cnt3)
#     line2 = line2_pattern
#     line3 = line3_pattern.format(Young[ei],0.3)
#     f.write(line1)
#     f.write(line2)
#     f.write(line3)

# f.close()

# visualise = True

#=============================================================#
# view
if args.view:
    v = fieldvi.Fieldvi()
    #v.addImageVolume(s.I, 'CT', renderArgs={'vmax':2000, 'vmin':-200})
    v.addImageVolume(s.I, 'CT', renderArgs={'vmax':PHANTOM_HU, 'vmin':WATER_HU})
    v.addData('centroids_img', centroids_img, scalar=E_binned, renderArgs={'mode':'point'})
    # v.addData('target points_inp', target_points_5[Young > np.min(Young)], scalar = Young[Young > np.min(Young)], renderArgs={'mode':'point', 'vmin':np.min(Young), 'vmax':np.max(Young), 'scale_mode':'none'})
    v.configure_traits()
    v.scene.background=(0,0,0)


