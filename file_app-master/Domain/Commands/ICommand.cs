using System.Threading.Tasks;

namespace Domain.Commands
{
    public interface ICommand<T, out TR, in TS>
    {
        Task<T> ExecuteAsync(TS state);
        T Execute(TS state);
        TR GetResult();
        T Result { get; }
    }
}