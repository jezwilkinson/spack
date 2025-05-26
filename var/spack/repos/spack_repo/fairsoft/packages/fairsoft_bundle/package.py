# Copyright 2013-2022 Lawrence Livermore National Security, LLC and other
#   Spack Project Developers. See the top-level COPYRIGHT file for details.
# Copyright 2020-2022 GSI Helmholtz Centre for Heavy Ion Research GmbH,
#   Darmstadt, Germany
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
from spack_repo.builtin.build_systems.bundle import BundlePackage
from spack.package import *


class FairsoftBundle(BundlePackage):
    """Provide some sort of 'include' for our environments"""

    homepage = "https://github.com/FairRootGroup/FairSoft"

    # To get only the flags, but no version pinnings:
    # For the next release (would love to call it "next", but that is
    # not sorted correctly by spack)
    version('may25')
    version('master')
    # Releases:

    variant('graphics', default=False)
    variant('mt', default=False)

    # Some normal packages
    depends_on('faircmakemodules')

    # Pin some variants:
    depends_on('geant4 ~threads', when='~mt')
    depends_on('geant4 +threads', when='+mt')
    depends_on('geant4 ~qt~vecgeom~opengl~x11~motif')

    # ensure that OpenBLAS uses CMake build system (default Makefile causes issues on some x86 Macs due to tests)
    depends_on('openblas build_system=cmake')
    
    # Generic ROOT dependencies
    depends_on('root +fortran+pythia8+vc~vdt')
    # Mostly for the experiments:
    depends_on('root +python+tmva+mlp+xrootd+sqlite')
    # FFTW for Panda
    depends_on('root +fftw')
    depends_on('fftw~mpi')
    depends_on('root +spectrum', when='@20.11:')
    depends_on('root ~x~opengl~aqua', when='~graphics')
    depends_on('root +x+opengl', when='+graphics')

    # Using 'platform=' in a when clause gets concretized too late.
    # and our root recipe disables +aqua on non-macOS now.
    # depends_on('root +aqua', when='+graphics platform=darwin')
    depends_on('root +aqua', when='+graphics')

    depends_on('pythia8@8.313', when='@may25')
    depends_on('root@6.36.00', when='@may25')
    depends_on('vmc@2-1', when='@may25')
    depends_on('geant3@4-4', when='@may25')
    depends_on('vgm@5-3-1', when='@may25')
    depends_on('geant4-vmc@6-7-p1', when='@may25')
    depends_on('fairsoft-config@develop', when='@may25', type='run')


    # next (master):
    depends_on('pythia8@8.310',          when='@master')
    # geant4 pinning breaks concretization
<<<<<<< HEAD
    depends_on("root@6.32.06",          when='@master')
    depends_on('vmc@2-0',            when='@master')
    depends_on('geant3@4-4',            when='@master')   # 4.2_fairsoft is not in the core spack !! 
    depends_on('vgm@5-3',               when='@master')   # 5.2 is not in the core spack !!
=======
    depends_on("root@6.30.04",          when='@master')
    depends_on('vmc@2-0',            when='@master')
    depends_on('geant3@4-1',            when='@master')   # 4.2_fairsoft is not in the core spack !! 
    depends_on('vgm@5-2',               when='@master')   # 5.2 is not in the core spack !!
>>>>>>> 9411118b7d (add fairsoft repo for testing)
    depends_on('geant4-vmc@6-5',        when='@master')   # 6.5 is not in the core spack !!
    depends_on('fairsoft-config@develop', when='@master', type='run')

