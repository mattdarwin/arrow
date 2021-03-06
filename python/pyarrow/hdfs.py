# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import posixpath

from pyarrow.util import implements
from pyarrow.filesystem import FileSystem
import pyarrow.lib as lib


class HadoopFileSystem(lib.HadoopFileSystem, FileSystem):
    """
    FileSystem interface for HDFS cluster. See pyarrow.hdfs.connect for full
    connection details
    """

    def __init__(self, host="default", port=0, user=None, kerb_ticket=None,
                 driver='libhdfs'):
        self._connect(host, port, user, kerb_ticket, driver)

    @implements(FileSystem.isdir)
    def isdir(self, path):
        return super(HadoopFileSystem, self).isdir(path)

    @implements(FileSystem.isfile)
    def isfile(self, path):
        return super(HadoopFileSystem, self).isfile(path)

    @implements(FileSystem.delete)
    def delete(self, path, recursive=False):
        return super(HadoopFileSystem, self).delete(path, recursive)

    @implements(FileSystem.mkdir)
    def mkdir(self, path, create_parents=True):
        return super(HadoopFileSystem, self).mkdir(path)

    @implements(FileSystem.rename)
    def rename(self, path, new_path):
        return super(HadoopFileSystem, self).rename(path, new_path)

    def ls(self, path, detail=False):
        """
        Retrieve directory contents and metadata, if requested.

        Parameters
        ----------
        path : HDFS path
        detail : boolean, default False
            If False, only return list of paths

        Returns
        -------
        result : list of dicts (detail=True) or strings (detail=False)
        """
        return super(HadoopFileSystem, self).ls(path, detail)

    def walk(self, top_path):
        """
        Directory tree generator for HDFS, like os.walk

        Parameters
        ----------
        top_path : string
            Root directory for tree traversal

        Returns
        -------
        Generator yielding 3-tuple (dirpath, dirnames, filename)
        """
        contents = self.ls(top_path, detail=True)

        directories, files = _libhdfs_walk_files_dirs(top_path, contents)
        yield top_path, directories, files
        for dirname in directories:
            for tup in self.walk(self._path_join(top_path, dirname)):
                yield tup


def _libhdfs_walk_files_dirs(top_path, contents):
    files = []
    directories = []
    for c in contents:
        scrubbed_name = posixpath.split(c['name'])[1]
        if c['kind'] == 'file':
            files.append(scrubbed_name)
        else:
            directories.append(scrubbed_name)

    return directories, files


def connect(host="default", port=0, user=None, kerb_ticket=None,
            driver='libhdfs'):
    """
    Connect to an HDFS cluster. All parameters are optional and should
    only be set if the defaults need to be overridden.

    Authentication should be automatic if the HDFS cluster uses Kerberos.
    However, if a username is specified, then the ticket cache will likely
    be required.

    Parameters
    ----------
    host : NameNode. Set to "default" for fs.defaultFS from core-site.xml.
    port : NameNode's port. Set to 0 for default or logical (HA) nodes.
    user : Username when connecting to HDFS; None implies login user.
    kerb_ticket : Path to Kerberos ticket cache.
    driver : {'libhdfs', 'libhdfs3'}, default 'libhdfs'
      Connect using libhdfs (JNI-based) or libhdfs3 (3rd-party C++
      library from Apache HAWQ (incubating) )

    Notes
    -----
    The first time you call this method, it will take longer than usual due
    to JNI spin-up time.

    Returns
    -------
    filesystem : HadoopFileSystem
    """
    fs = HadoopFileSystem(host=host, port=port, user=user,
                          kerb_ticket=kerb_ticket, driver=driver)
    return fs
