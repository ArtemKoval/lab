using System;

namespace NFS
{
    public struct NPath
        : IEquatable<NPath>,
            IComparable<NPath>
    {
        public string Raw { get; }

        public NPath(string raw)
        {
            Raw = raw;
        }
        
        public bool Equals(NPath other)
        {
            throw new NotImplementedException();
        }

        public int CompareTo(NPath other)
        {
            throw new NotImplementedException();
        }
    }
}