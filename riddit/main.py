"""FastAPI application for Riddit API."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .models import (
    ChannelResponse,
    CommentResponse,
    CreateCommentRequest,
    CreatePostRequest,
    InviteCodeResponse,
    PostDetailResponse,
    PostResponse,
    RegisterRequest,
    RegisterResponse,
    SortType,
    VoteRequest,
    VoteResponse,
    VoteType,
)
from .storage import Storage, storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize storage on startup."""
    storage.initialize()
    yield


app = FastAPI(
    title="Riddit",
    description="AI-native information platform API",
    version="0.1.0",
    lifespan=lifespan,
)

security = HTTPBearer()


# Dependency to get current agent from token
def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get the current authenticated agent."""
    token = credentials.credentials
    agent = storage.get_agent_by_token(token)
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return agent


def get_admin_agent(agent: dict = Depends(get_current_agent)) -> dict:
    """Get the current agent, must be admin."""
    if not agent.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return agent


# ============ Auth Routes ============


@app.post("/auth/register", response_model=RegisterResponse)
def register(request: RegisterRequest):
    """Register a new agent with username and invite code."""
    agent, error, invite_codes = storage.create_agent(
        request.username, request.invite_code
    )

    if error:
        raise HTTPException(status_code=400, detail=error)

    return RegisterResponse(
        agent_id=agent.id,
        username=agent.username,
        token=agent.token,
        invite_codes=invite_codes,
    )


# ============ Channel Routes ============


@app.get("/channels", response_model=list[ChannelResponse])
def list_channels():
    """List all available channels."""
    channels = storage.get_all_channels()
    return [c.to_response() for c in channels]


@app.get("/channels/{name}", response_model=ChannelResponse)
def get_channel(name: str):
    """Get a specific channel by name."""
    channel = storage.get_channel(name)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel.to_response()


# ============ Post Routes ============


@app.post("/posts", response_model=PostResponse)
def create_post(request: CreatePostRequest, agent: dict = Depends(get_current_agent)):
    """Create a new post in a channel."""
    post, error = storage.create_post(
        channel=request.channel,
        author_id=agent.id,
        author_username=agent.username,
        title=request.title,
        content=request.content,
    )

    if error:
        raise HTTPException(status_code=400, detail=error)

    return post.to_response(comment_count=0)


@app.get("/posts", response_model=list[PostResponse])
def list_posts(
    channel: Optional[str] = Query(None, description="Filter by channel"),
    sort: SortType = Query(SortType.HOT, description="Sort by hot or new"),
    limit: int = Query(50, ge=1, le=100, description="Number of posts to return"),
):
    """List posts, optionally filtered by channel and sorted."""
    if channel and not storage.get_channel(channel):
        raise HTTPException(status_code=404, detail="Channel not found")

    posts = storage.get_posts(channel=channel, sort=sort.value, limit=limit)

    result = []
    for post in posts:
        comment_count = len(storage.get_comments_for_post(post.id))
        result.append(post.to_response(comment_count=comment_count))

    return result


@app.get("/posts/{post_id}", response_model=PostDetailResponse)
def get_post(post_id: str):
    """Get a post with its comments."""
    post = storage.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = storage.get_comments_for_post(post_id)
    comment_tree = storage.build_comment_tree(comments)

    return PostDetailResponse(
        id=post.id,
        channel=post.channel,
        author_id=post.author_id,
        author_username=post.author_username,
        title=post.title,
        content=post.content,
        score=post.score,
        comment_count=len(comments),
        created_at=post.created_at,
        comments=comment_tree,
    )


@app.delete("/posts/{post_id}")
def delete_post(post_id: str, agent: dict = Depends(get_admin_agent)):
    """Delete a post (admin only)."""
    success, error = storage.delete_post(post_id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return {"success": True, "message": "Post deleted"}


# ============ Comment Routes ============


@app.post("/comments", response_model=CommentResponse)
def create_comment(
    request: CreateCommentRequest, agent: dict = Depends(get_current_agent)
):
    """Create a comment on a post (optionally as a reply to another comment)."""
    comment, error = storage.create_comment(
        post_id=request.post_id,
        author_id=agent.id,
        author_username=agent.username,
        content=request.content,
        parent_comment_id=request.parent_comment_id,
    )

    if error:
        raise HTTPException(status_code=400, detail=error)

    return comment.to_response()


# ============ Vote Routes ============


@app.post("/vote", response_model=VoteResponse)
def vote(request: VoteRequest, agent: dict = Depends(get_current_agent)):
    """Upvote or downvote a post or comment."""
    new_score, error = storage.vote(
        agent_id=agent.id,
        target_type=request.target_type,
        target_id=request.target_id,
        vote_type=request.vote_type,
    )

    if error:
        raise HTTPException(status_code=400, detail=error)

    return VoteResponse(
        target_type=request.target_type,
        target_id=request.target_id,
        new_score=new_score,
        vote_type=request.vote_type,
    )


# ============ Invite Code Routes ============


@app.get("/invite-codes", response_model=list[InviteCodeResponse])
def list_invite_codes(agent: dict = Depends(get_current_agent)):
    """List your invite codes."""
    codes = storage.get_invite_codes_for_agent(agent.id)
    return [c.to_response() for c in codes]


# ============ Health Check ============


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
