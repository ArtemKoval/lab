using System;
using System.IO;
using NFS;

namespace RuntimeTest
{
    class Program
    {
        static void Main(string[] args)
        {
            var fs = new PhysicalFileSystem();
//            foreach (var dir in fs.EnumerateDirectories(Directory.GetCurrentDirectory()))
//            {
//                Console.WriteLine(dir);
//            }
//            
//            foreach (var path in fs.EnumeratePaths(Directory.GetCurrentDirectory()))
//            {
//                Console.WriteLine(path);
//            }

//            fs.CreateFile(new NPath(Directory.GetCurrentDirectory()) / new NPath("test1.txt"));
//            
//            foreach (var file in fs.EnumerateFiles(Directory.GetCurrentDirectory()))
//            {
//                Console.WriteLine(file);
//            }
        }
    }
}