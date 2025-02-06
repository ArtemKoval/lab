namespace Domain.Commands
{
    public interface IUploadFileCommand<T, out TR, in TS>
        : ICommand<T, TR, TS>
    {
    }
}