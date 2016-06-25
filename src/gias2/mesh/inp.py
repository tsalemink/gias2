"""
FILE: inp.py
LAST MODIFIED: 24-12-2015 
DESCRIPTION:
classes and functions for reading and writing .inp files for
ABAQUS and FEBio

===============================================================================
This file is part of GIAS2. (https://bitbucket.org/jangle/gias2)

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
===============================================================================
"""

COMMENTCHARS = '**'
ELEMNODES = {'C3D8R': 8,
             'R3D3': 3,
             'R3D4': 4,
             'C3D4': 4,
             'T3D2': 2, 
             'S3': 3,
             'S4': 4,
             }

class Mesh(object):
    """ ABAQUS INP Mesh object
    """

    def __init__(self, name):
        self.name = name
        self.nodes = None
        self.nodeNumbers = None
        self.elems = None
        self.elemNumbers = None
        self.elemType = None

    def getName(self):
        return name

    def setNodes(self, nodes, nodeNumbers):
        """ Set nodes of the mesh.
        Arguments:
        nodes : a list containing lists of node coordinates
        nodeNumbers : a list of node numbers corresponding to their
                      coordinate.
        """
        self.nodes = nodes
        self.nodeNumbers = nodeNumbers

    def getNode(self, nodeNumber):
        """Returns the coordinates of the node with node number
        nodeNumber
        """
        return self.nodes[self.nodeNumbers.index(nodeNumber)]

    def getNodes(self):
        """Returns a list of all node coordinates
        """
        return self.nodes

    def getNumberOfNodes(self):
        """Returns the total number of nodes
        """
        return len(self.nodes)

    def setElems(self, elems, elemNumbers, elemType):
        """Set elements of the mesh.
        Arguments:
        elems: a list containing the lists of the node numbers of each 
                element
        elemNumbers: a list of element numbers corresponding to its node lists
        elemType: a string of the ABAQUS element type 
        """
        self.elems = elems
        self.elemNumbers = elemNumbers
        self.elemType = elemType

    def getElem(self, elemNumber):
        """Returns the node numbers of the element with element number
        elemNumber
        """
        return self.elems[self.elemNumbers.index(elemNumber)]

    def getElems(self):
        """Returns a list of all elements' node numbers
        """
        return self.elems

    def getElemType(self):
        """Returns the element type string
        """
        return self.elemType

    def getNumberOfElems(self):
        """Returns the total number of elements
        """
        return len(self.elems)


class InpReader(object):
    """INP reading class
    """

    nodeStartString = '*NODE'

    def __init__(self, filename):
        self.filename = filename
        self.meshNames = None

    def readHeader(self):
        """Reads and returns the file header
        """
        header = []
        with open(self.filename, 'r') as f:
            doScan = 1
            while doScan:
                l = next(f)
                if l==(COMMENTCHARS+'\n'):
                    doScan = 0
                elif l[:2]!=COMMENTCHARS:
                    doScan = 0
                else:
                    header.append(l[2:].strip())

        return header

    def readMeshNames(self):
        """Read and returns a set of all the ELSET names in the file
        """
        meshNames = set()
        with open(self.filename, 'r') as f:
            doScan = 1
            while doScan:
                try:
                    l = next(f)
                except StopIteration:
                    doScan = 0
                else:
                    if 'ELSET' in l:
                        for term in l.split(','):
                            if 'ELSET' in term:
                                if term=='*ELSET':
                                    break
                                else:
                                    meshNames.add(term.split('=')[1].strip())
                                    break

        self.meshNames = list(meshNames)
        return self.meshNames

    def readMesh(self, meshName):
        """Reads and returns the mesh with name meshName.
        Arguments:
        meshName: string matching an NSET/ELSET name in the file
        Returns:
        mesh: a Mesh instance with the read-in mesh parameters
        """
        nodeNumbers = []
        nodes = []

        elemType = None
        elemNumbers = []
        elems = []

        # read nodes
        with open(self.filename, 'r') as f:
            doScan = 1
            while doScan:
                try:
                    l = next(f)
                except StopIteration:
                    raise IOError('No NSET named '+meshName)
                else:
                    # if ('NSET='+meshName) in l:
                    if (self.nodeStartString) in l:
                        doScan = 0

            doScan = 1
            while doScan:
                l = next(f).strip()
                if '*' not in l:
                    terms = l.split(',')
                    nodeNumbers.append(int(terms[0]))
                    nodes.append([float(t) for t in terms[1:]])
                else:
                    doScan = 0

            print(('loaded %d nodes'%(len(nodes))))

        # read elements
        with open(self.filename, 'r') as f:
            doScan = 1
            while doScan:
                try:
                    l = next(f)
                except StopIteration:
                    raise IOError('No ELSET named '+meshName)
                else:
                    if ('ELSET='+meshName) in l:
                        doScan = 0
                        for term in l.split(','):
                            if 'TYPE' in term.upper():
                                elemType = term.split('=')[1].strip()
            
            try:
                en = ELEMNODES[elemType]
            except KeyError:
                raise RuntimeError('Unsupported element type: '+elemType)

            # doScan = 1
            # while doScan:
            #   l = f.next().strip()
            #   if '*' not in l:
            #       terms = l.split(',')
            #       print terms
            #       elemNumbers.append(int(terms[0]))
            #       elems.append([int(t) for t in terms[1:]])
            #   else:
            #       doScan = 0

            doScan = 1
            nCount = -1
            elem = []
            while doScan:
                try:
                    l = next(f).strip()
                except StopIteration:
                    doScan = 0
                else:
                    if '*' not in l:
                        terms = [int(i) for i in l.split(',') if i]
                        if len(terms)==0:
                            terms = [int(l.strip())]
                        for t in terms:
                            if nCount==-1:
                                elemNumbers.append(t)
                                nCount += 1
                            elif nCount<en:
                                elem.append(t)
                                nCount += 1
                                if nCount==en:
                                    elems.append(elem)
                                    elem = []
                                    nCount = -1
                            else:
                                # should be here something bad happened
                                raise RuntimeError

                        # elemNumbers.append(int(terms[0]))
                        # elems.append([int(t) for t in terms[1:]])
                    else:
                        doScan = 0

            print(('loaded %s %s elements'%(len(elems), elemType)))

        mesh = Mesh(meshName)
        mesh.setNodes(nodes, nodeNumbers)
        mesh.setElems(elems, elemNumbers, elemType)

        return mesh

    def readAllMeshes(self):
        """Read in all meshes in the file.
        Returns a dictionary in which keys are mesh names and values are the
        meshes.
        """
        meshNames = self.readMeshNames()
        meshes = {}
        for mn in meshNames:
            meshes[mn] = self.readMesh(mn)

        return meshes


class InpWriter(object):

    _commentChars = '**'
    _nodeHeaderLine = '*NODE, NSET={}\n'
    _nodeCounterFormat = '{:6d}'
    _nodeCoordFormat = '{:16.10f}'
    _elemHeaderLine = '*ELEMENT, TYPE={}, ELSET={}\n'
    _elemCounterFormat = '{:6d}'
    _elemNodeFormat = '{:10d}'

    def __init__(self, filename, autoFormat=True):
        self._meshes = []
        self.filename = filename
        self._header = None
        self.autoFormat = autoFormat
    
    def addHeader(self, header):
        """
        Add commented text to be written at the top of the 
        file.
        """
        self._header = header
        if header[-1:]!='\n':
            self._header = self._header+'\n'

    def addMesh(self, mesh):
        """Add a mesh to be written.
        Argument:
        mesh : a Mesh object
        """

        self._meshes.append(mesh)

    def _autoFormat(self):
        maxNodes = max([max(mesh.nodeNumbers) for mesh in self._meshes])
        nodeCounterCharLength = len(str(maxNodes)) + 1
        self._nodeCounterFormat = '{:'+str(nodeCounterCharLength)+'}'
        
        maxElems = max([max(mesh.elemNumbers) for mesh in self._meshes])
        elemCounterCharLength = len(str(maxElems)) + 1
        self._elemCounterFormat = '{:'+str(elemCounterCharLength)+'}'
        self._elemNodeFormat = '{:'+str(nodeCounterCharLength)+'}'

    def write(self):
        """
        Write data to file.
        """
        
        if len(self._meshes)==0:
            raise RuntimeError('no meshes defined')

        if self.autoFormat:
            self._autoFormat()

        # open file for writing
        with open(self.filename, 'w') as f:
            # write header comments
            if self._header!=None:
                f.write(COMMENTCHARS+self._header)
            else:
                f.write(COMMENTCHARS+'\n')

            f.write(COMMENTCHARS+'\n')

            # write each mesh
            for mesh in self._meshes:

                # nodes
                if mesh.nodes is not None:
                    f.write(self._nodeHeaderLine.format(mesh.name))
                    for ni, n in enumerate(mesh.nodes):
                        f.write(self._getNodeLine(mesh.nodeNumbers[ni], n))

                    f.write(COMMENTCHARS+'\n')

                # elems
                if mesh.elems is not None:
                    f.write(self._elemHeaderLine.format(mesh.elemType, mesh.name))
                    for ei, e in enumerate(mesh.elems):
                        f.write(self._getElemLine(mesh.elemNumbers[ei], e))

                    f.write(COMMENTCHARS+'\n')

    def _getNodeLine(self, i, node):
        words = [self._nodeCounterFormat.format(i),] +\
                [self._nodeCoordFormat.format(x) for x in node]

        return ', '.join(words)+'\n'

    def _getElemLine(self, i, elem):
        words = [self._elemCounterFormat.format(i),] +\
                [self._elemNodeFormat.format(n) for n in elem]

        return ', '.join(words)+'\n'




