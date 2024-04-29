from tortoise import models, fields


class User(models.Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=212)


class Category(models.Model):
    id = fields.IntField(pk=True, generated=True)
    name = fields.CharField(max_length=212)

    def __str__(self):
        return self.name


class Tag(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=212)

    def __str__(self):
        return self.name


class Post(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=212)
    image = fields.CharField(max_length=212)
    description = fields.TextField()
    author = fields.ForeignKeyField('models.User', related_name='articles')
    category = fields.ForeignKeyField('models.Category', related_name='articles')
    tags = fields.ManyToManyField('models.Tag', related_name='articles')

    def __str__(self):
        return self.name

    class Meta:
        table_name = 'posts'
