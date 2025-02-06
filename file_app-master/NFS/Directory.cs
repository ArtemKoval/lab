namespace NFS
{
    public class Directory : IFileSystemEntry
    {
        public Directory(string name,
            long length,
            NPath path)
        {
            Name = name;
            Length = length;
            Path = path;
        }

        public string Name { get; private set; }
        public string FullName => Path.Raw;
        public long Length { get; private set; }
        public NPath Path { get; private set; }
    }
}