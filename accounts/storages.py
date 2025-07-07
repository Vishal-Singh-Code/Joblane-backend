from cloudinary_storage.storage import MediaCloudinaryStorage

class RawMediaCloudinaryStorage(MediaCloudinaryStorage):
    """
    Custom storage class for handling non-image files (like PDF resumes) as raw files in Cloudinary.
    """
    def __init__(self, *args, **kwargs):
        kwargs['resource_type'] = 'raw'
        super().__init__(*args, **kwargs)
