namespace Domain.Commands
{
    public interface ICopyCommand<T, out TR, in TS>
        : ICommand<T, TR, TS>
    {
    }
}