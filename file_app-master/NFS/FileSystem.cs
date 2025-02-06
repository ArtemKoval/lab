using System;
using System.Collections.Generic;
using System.IO;

namespace NFS
{
    public abstract class FileSystem : IFileSystem
    {
        public void Dispose()
        {
        }

        protected virtual void CreateDirectoryImplementation(NPath path)
        {
            throw new NotImplementedException();
        }

        public void CreateDirectory(NPath path)
        {
            CreateDirectoryImplementation(path);
        }

        protected virtual bool DirectoryExistsImplementation(NPath path)
        {
            throw new NotImplementedException();
        }

        public bool DirectoryExists(NPath path)
        {
            return DirectoryExistsImplementation(path);
        }

        protected virtual void MoveDirectoryImplementation(NPath srcPath, NPath destPath)
        {
            throw new NotImplementedException();
        }

        public void MoveDirectory(NPath srcPath, NPath destPath)
        {
            MoveDirectoryImplementation(srcPath, destPath);
        }

        protected virtual void DeleteDirectoryImplementation(NPath path, bool isRecursive)
        {
            throw new NotImplementedException();
        }

        public void DeleteDirectory(NPath path, bool isRecursive)
        {
            DeleteDirectoryImplementation(path, isRecursive);
        }

        public void ReplaceFile(NPath srcPath, NPath destPath, NPath destBackupPath, bool ignoreMetadataErrors)
        {
            throw new NotImplementedException();
        }

        protected virtual void CopyFileImplementation(NPath srcPath, NPath destPath, bool overwrite)
        {
            throw new NotImplementedException();
        }

        public void CopyFile(NPath srcPath, NPath destPath, bool overwrite)
        {
            CopyFileImplementation(srcPath, destPath, overwrite);
        }

        protected virtual void MoveFileImplementation(NPath srcPath, NPath destPath)
        {
            throw new NotImplementedException();
        }

        public void MoveFile(NPath srcPath, NPath destPath)
        {
            MoveFileImplementation(srcPath, destPath);
        }

        protected virtual bool FileExistsImplementation(NPath path)
        {
            throw new NotImplementedException();
        }

        public bool FileExists(NPath path)
        {
            return FileExistsImplementation(path);
        }

        protected virtual void DeleteFileImplementation(NPath path)
        {
            throw new NotImplementedException();
        }

        public void DeleteFile(NPath path)
        {
            DeleteFileImplementation(path);
        }

        protected virtual Stream OpenFileImplementation(NPath path, FileMode mode, FileAccess access,
            FileShare share = FileShare.None)
        {
            throw new NotImplementedException();
        }

        public Stream OpenFile(NPath path, FileMode mode, FileAccess access, FileShare share = FileShare.None)
        {
            return OpenFileImplementation(path, mode, access, share);
        }

        public long GetFileLength(NPath path)
        {
            throw new NotImplementedException();
        }

        public IEnumerable<NPath> EnumeratePaths(NPath path, string searchPattern)
        {
            throw new NotImplementedException();
        }

        public FileAttributes GetAttributes(NPath path)
        {
            throw new NotImplementedException();
        }

        public void SetAttributes(NPath path, FileAttributes attributes)
        {
            throw new NotImplementedException();
        }

        public DateTime GetCreationTime(NPath path)
        {
            throw new NotImplementedException();
        }

        public void SetCreationTime(NPath path, DateTime time)
        {
            throw new NotImplementedException();
        }

        public void SetLastAccessTime(NPath path, DateTime time)
        {
            throw new NotImplementedException();
        }

        public void SetLastWriteTime(NPath path, DateTime time)
        {
            throw new NotImplementedException();
        }

        public DateTime GetLastAccessTime(NPath path)
        {
            throw new NotImplementedException();
        }

        protected virtual DateTime GetLastWriteTimeImplementation(NPath path)
        {
            throw new NotImplementedException();
        }

        public DateTime GetLastWriteTime(NPath path)
        {
            return GetLastWriteTimeImplementation(path);
        }

        public string ConvertPathToInternal(NPath path)
        {
            throw new NotImplementedException();
        }

        public NPath ConvertPathFromInternal(string systemPath)
        {
            throw new NotImplementedException();
        }

        protected virtual NPath PathCombineImplementation(NPath path1, NPath path2)
        {
            throw new NotImplementedException();
        }

        public NPath PathCombine(NPath path1, NPath path2)
        {
            return PathCombineImplementation(path1, path2);
        }

        protected virtual IEnumerable<File> EnumerateFileEntriesImplementation(NPath path)
        {
            throw new NotImplementedException();
        }

        public IEnumerable<File> EnumerateFileEntries(NPath path)
        {
            return EnumerateFileEntriesImplementation(path);
        }

        protected virtual IEnumerable<Directory> EnumerateDirectoriesImplementation(NPath path)
        {
            throw new NotImplementedException();
        }

        public IEnumerable<Directory> EnumerateDirectories(NPath path)
        {
            return EnumerateDirectoriesImplementation(path);
        }
    }
}