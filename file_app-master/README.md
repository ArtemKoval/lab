## Prerequisites

* .NET Core 2.1

## How to start

1. Open VS (or Rider) FileApp.sln
2. Choose Web: IIS Express profile
3. Click "Run"
4. Visit http://localhost:5000 in your browser (if not opened automatically)

## Implementation notes

* Specifically omitted test project to save time
* No defensive coding to save time
* No comments to validate design readability

## ASP.NET File Application

File Application is an ASP.NET AJAX application that lets the user upload, store, browse, and copy folders and files on a web server.

The application supports the following functionality:
* A treeview to browse folders and files on the server, similar to the left-hand pane in Windows Explorer.
The treeview shows all of the available content: folders and files.
The user is able to select an individual item in the treeview and perform actions on that item.  The actions may be run via a button-invoked menu or a context-sensitive right-click menu.
* All items (files and folders) support the following actions:
    * Delete
    * Rename
    * Copy: this action creates a copy of the item A and places this copy in the same folder, with the name “Copy of A”.  When a folder is copied, all of its sub-folders and files should be copied as well (a “deep” copy).
* Files support the additional action:
    * Download: this action should stream the file to the user’s browser
* Folders support these additional actions:
    * Create new sub-folder
    * Upload a file from the client’s hard drive to the folder (requires a mechanism to select the file to be uploaded)
* Meta-date is displayed on the right-side panel
* File meta-data:
    * Size
    * Last modified time
* Folder meta-data:
    * Cumulative size of all files in the sub-tree rooted at the folder
    * Last modified time

Communication with the server is done asynchronously (using AJAX or similar mechanism) to minimize full-page post-backs.

## Design notes

1. There is a self-contained object model representing the folder/file structure.
It's in the NFS project. NFS stands for "Normalized File System" (NPath stands for "Normalized Path").
The idea is to enhance this system in the future to support platform-agnostic way to join various file systems.

2. This business-layer object model is decoupled from UI code in the Domain project.
It utilizes a number of Commands which are managed by FileSystemService.
The C# objects representing files and folders make no reference to UI libraries at all.

3. It is anticipated that in the future, the application will support new types of items, in addition to regular files and folders.  The new items would require special processing on upload and download, and support new types of actions (such as “Edit” and “View”).
The overall system design allows it easily support new types of items and new kinds of actions, while changing existing classes as little as possible. First extension point is providing more FileSystemEntries by implementing IFileSystemEntry interface. Second extension point is adding more Commands.

3. In the real world, user’s data would be persisted in a database.
Logical structure (which FileSystemEntities belong to which user) should be stored in the DB. The actual files should be stroed in the external file system. Overall design should be classical number of tables: one-to-many User-FileSystemEntities (or many-to-many if sharing is going to be supported), one-to-many FileSystemEntity-FileSystemEntity (to support logical grouping of folders-files), EntityTypes with the associated allowed EntityActions.

## System/environment requirements

* MS Visual Studio/JetBrains Rider, C#.
* https://webix.com/filemanager/ is used to provide basic file management layout.