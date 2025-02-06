using System.Collections.Generic;

namespace Domain.FileSystem
{
    public class TreeDTO
    {
        public string Id;

        public string Value;

        public string Type;

        public long Date;

        public long Size;

        public List<TreeDTO> Data = new List<TreeDTO>();
    }
}