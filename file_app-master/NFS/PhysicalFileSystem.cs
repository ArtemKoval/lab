using System;
using System.Collections.Generic;
using System.IO;

namespace NFS
{
    public class PhysicalFileSystem : FileSystem
    {
        protected override DateTime GetLastWriteTimeImplementation(NPath path)
        {
            return System.IO.File.GetLastWriteTime(path.Raw);
        }

        protected override Stream OpenFileImplementation(
            NPath path,
            FileMode mode,
            FileAccess access,
            FileShare share = FileShare.None)
        {
            return new FileStream(path.Raw, mode, access, share);
        }

        protected override bool FileExistsImplementation(NPath path)
        {
            return System.IO.File.Exists(path.Raw);
        }

        protected override bool DirectoryExistsImplementation(NPath path)
        {
            return System.IO.Directory.Exists(path.Raw);
        }

        protected override IEnumerable<File> EnumerateFileEntriesImplementation(NPath path)
        {
            var files = System.IO.Directory.GetFiles(path.Raw);

            foreach (var file in files)
            {
                yield return new File(
                    Path.GetFileName(file),
                    new FileInfo(file).Length,
                    new NPath(file));
            }
        }

        protected override IEnumerable<Directory> EnumerateDirectoriesImplementation(NPath path)
        {
            var directories = System.IO.Directory.GetDirectories(path.Raw);

            foreach (var directory in directories)
            {
                yield return new Directory(
                    Path.GetDirectoryName(directory),
                    0,
                    new NPath(directory)
                );
            }
        }

        protected override void DeleteDirectoryImplementation(NPath path, bool isRecursive)
        {
            var folder = new DirectoryInfo(path.Raw);
            folder.Delete(isRecursive);
        }

        protected override void DeleteFileImplementation(NPath path)
        {
            var file = new FileInfo(path.Raw);
            file.Delete();
        }

        protected override NPath PathCombineImplementation(NPath path1, NPath path2)
        {
            var path = Path.Combine(
                path1.Raw,
                path2.Raw);

            return new NPath(path);
        }

        protected override void MoveDirectoryImplementation(NPath srcPath, NPath destPath)
        {
            System.IO.Directory.Move(srcPath.Raw, destPath.Raw);
        }

        protected override void MoveFileImplementation(NPath srcPath, NPath destPath)
        {
            System.IO.File.Move(srcPath.Raw, destPath.Raw);
        }

        protected override void CreateDirectoryImplementation(NPath path)
        {
            System.IO.Directory.CreateDirectory(path.Raw);
        }

        protected override void CopyFileImplementation(NPath srcPath, NPath destPath, bool overwrite)
        {
            System.IO.File.Copy(srcPath.Raw, destPath.Raw, overwrite);
        }
    }
}