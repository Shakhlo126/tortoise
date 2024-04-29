from typing import List
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, status, UploadFile, File
from tortoise import Tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.contrib.fastapi import register_tortoise
from models import Category, Tag, User, Post
from tortoise.transactions import in_transaction

app = FastAPI(title='Blog API', description='blog app', version='1.0')


async def init_db():
    await Tortoise.init(
        db_url="sqlite://db.sqlite3",
        modules={"models": ["models"]}
    )
    await Tortoise.generate_schemas()


register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["models"]}
)


class CategoryIn(BaseModel):  # Pydantic modelini yaratish
    name: str = Field(..., min_length=1)  # Minimal uzunlikni chegaralash


class TagIn(BaseModel):  # Tag uchun Pydantic modelini yaratish
    name: str


class AuthorIn(BaseModel):
    username: str


class PostIn(BaseModel):
    id: int
    name: str
    description: str
    category_id: int
    author_id: int
    tags: List[TagIn]

    class Config:
        from_attributes = True


Category_model = pydantic_model_creator(Category, name="Category")
Post_model = pydantic_model_creator(Post, name="Post")
Tag_model = pydantic_model_creator(Tag, name="Tag")
Author_model = pydantic_model_creator(User, name="User")


@app.on_event("startup")
async def startup():
    await init_db()


@app.post('/category', response_model=Category_model)
async def create_category(category: CategoryIn):
    async with in_transaction() as tnx:
        new_cat = await Category.create(name=category.name)
        await tnx.commit()
        return new_cat


@app.post('/author', response_model=Author_model)
async def create_author(author: AuthorIn):
    async with in_transaction() as tnx:
        authors = await User.create(username=author.username)
        await tnx.commit()
        return authors


@app.post('/tag', response_model=Tag_model)
async def create_tag(tag: TagIn):
    new_tag = await Tag.create(name=tag.name)
    return new_tag


@app.get('/category')
async def get_categories():
    return await Category.all()


@app.get('/category/{pk}')
async def get_category(pk: int):
    category = await Category_model.from_queryset_single(Category.get(id=pk))
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category does not exist")
    return category


@app.post('/posts')
async def create_post(author_id: int, category_id: int, name: str, description: str, tags: List[str],
                      image: UploadFile = File(...)):
    with open(f"images/{image.filename}", "wb") as f:
        f.write(image.file.read())
    image_path = f"images/{image.filename}"
    category = await Category.get(id=category_id)
    author = await User.get(id=author_id)
    tags_objects = [await Tag.get_or_none(name=tag) for tag in tags]
    post = await Post.create(name=name, description=description, author=author, image=image_path,
                             category=category, )
    await post.tags.add(*[tag for tag in tags_objects if tag is not None])
    return post


#
# @app.get('/posts/{pk}', response_model=PostIn)
# async def get_post(pk: int):
#     post = await Post.get(id=pk)
#     if not post:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post does not exist")
#     return post

@app.get('/posts/{pk}', response_model=PostIn)
async def get_post(pk: int):
    post = await Post.get_or_none(id=pk)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Extract tags data from the many-to-many relation
    tags_data = await post.tags.all()
    tags_list = [Tag_model.from_orm(tag) for tag in tags_data]

    # Get the category and author data
    category_data = await post.category
    author_data = await post.author

    # Return the post data with all required fields
    return {
        **Post_model.from_orm(post).dict(),
        'tags': tags_list,
        'category_id': category_data.id,
        'author_id': author_data.id
    }
