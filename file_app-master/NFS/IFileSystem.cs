using System;
using System.Collections.Generic;
using System.IO;

namespace NFS
{
    public interface IFileSystem : IDisposable
    {
        void CreateDirectory(NPath path);

        bool DirectoryExists(NPath path);

        void MoveDirectory(NPath srcPath, NPath destPath);

        void DeleteDirectory(NPath path, bool isRecursive);

        void ReplaceFile(NPath srcPath, NPath destPath, NPath destBackupPath, bool ignoreMetadataErrors);

        void CopyFile(NPath srcPath, NPath destPath, bool overwrite);

        void MoveFile(NPath srcPath, NPath destPath);

        bool FileExists(NPath path);

        void DeleteFile(NPath path);

        Stream OpenFile(NPath path, FileMode mode, FileAccess access, FileShare share = FileShare.None);

        long GetFileLength(NPath path);
        
        IEnumerable<NPath> EnumeratePaths(NPath path, string searchPattern);

        FileAttributes GetAttributes(NPath path);

        void SetAttributes(NPath path, FileAttributes attributes);

        DateTime GetCreationTime(NPath path);

        void SetCreationTime(NPath path, DateTime time);

        void SetLastAccessTime(NPath path, DateTime time);

        void SetLastWriteTime(NPath path, DateTime time);

        DateTime GetLastAccessTime(NPath path);

        DateTime GetLastWriteTime(NPath path);

        string ConvertPathToInternal(NPath path);

        NPath ConvertPathFromInternal(string systemPath);

        NPath PathCombine(NPath path1, NPath path2);

        IEnumerable<File> EnumerateFileEntries(NPath path);

        IEnumerable<Directory> EnumerateDirectories(NPath path);
    }
}