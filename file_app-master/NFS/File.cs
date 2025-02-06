namespace NFS
{
    public class File : IFileSystemEntry
    {
        public File(string name,
            long length,
            NPath path)
        {
            Name = name;
            Length = length;
            Path = path;
        }

        public string Name { get; private set; }
        public long Length { get; private set; }
        public string FullName => Path.Raw;
        public NPath Path { get; private set; }
    }
}