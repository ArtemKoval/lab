namespace NFS
{
    public interface IFileSystemEntry
    {
        string Name { get;}

        long Length { get; }
        
        string FullName { get; }

        NPath Path { get;}
    }
}