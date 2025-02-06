using Microsoft.AspNetCore.Http;
// ReSharper disable UnusedAutoPropertyAccessor.Global

// ReSharper disable InconsistentNaming

namespace Web.DTO
{
    public class UploadRequest
    {
        public IFormFile upload { get; set; }
        public string upload_fullpath { get; set; }
        public string action { get; set; }
        public string target { get; set; }
    }
}