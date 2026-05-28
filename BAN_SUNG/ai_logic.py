"""ai_logic.py — BFS, DFS, A* pathfinding + heuristic prediction with 8-directional support & smoothing."""
from collections import deque
import heapq
import math
from constants import TILE_SIZE


# 8 Directions with their cost (orthogonal = 1.0, diagonal = 1.414)
DIRS_8 = [
    (0, -1, 1.0), (0, 1, 1.0), (-1, 0, 1.0), (1, 0, 1.0),
    (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)
]


def tile(px, py):
    return int(px // TILE_SIZE), int(py // TILE_SIZE)


# ── Visibility check ─────────────────────────────────────────────────────────
def has_line_of_sight(x1, y1, x2, y2, game_map, steps=15, radius=0):
    """Bresenham-style LOS check with optional collision radius check."""
    # 1. Fast check: check points along the line without radius first
    for i in range(steps + 1):
        t  = i / steps
        px = x1 + (x2 - x1) * t
        py = y1 + (y2 - y1) * t
        if game_map.is_wall_pixel(px, py):
            return False
            
    # 2. Radius check if radius > 0
    if radius > 0:
        for i in range(steps + 1):
            t  = i / steps
            px = x1 + (x2 - x1) * t
            py = y1 + (y2 - y1) * t
            if game_map.is_wall_pixel_radius(px, py, radius):
                return False
    return True


def smooth_pixel_path(path, game_map, radius_px=10):
    """
    Smooth a pixel-based path by skipping unnecessary waypoints.
    If there is direct line of sight between waypoints (checked with a safety radius),
    we connect them directly to make movement look professional.
    """
    safe_radius = radius_px
    
    if not path or len(path) <= 2:
        return path
    
    smoothed = [path[0]]
    curr_idx = 0
    n = len(path)
    
    while curr_idx < n - 1:
        next_idx = curr_idx + 1
        # Look ahead up to 8 nodes (giảm từ 10 để tránh skip quá xa)
        max_lookahead = min(n, curr_idx + 8)
        for test_idx in range(max_lookahead - 1, curr_idx + 1, -1):
            x1, y1 = path[curr_idx]
            x2, y2 = path[test_idx]
            # Calculate dynamic steps based on distance (one step per 12 pixels)
            dist = math.hypot(x2 - x1, y2 - y1)
            steps = max(4, int(dist / 12))
            if has_line_of_sight(x1, y1, x2, y2, game_map, steps=steps, radius=safe_radius):
                next_idx = test_idx
                break
        smoothed.append(path[next_idx])
        curr_idx = next_idx
        
    return smoothed


def find_fallback_destination(gx, gy, game_map):
    """Finds the nearest walkable tile to (gx, gy) within a 3-tile radius using BFS."""
    if not game_map.is_wall(gx, gy):
        return gx, gy
        
    queue = deque([(gx, gy)])
    visited = {(gx, gy)}
    
    while queue:
        cx, cy = queue.popleft()
        if not game_map.is_wall(cx, cy):
            return cx, cy
            
        if abs(cx - gx) > 3 or abs(cy - gy) > 3:
            continue
            
        for dx, dy, _ in DIRS_8:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < game_map.width and 0 <= ny < game_map.height:
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
    return None


# ── BFS — shortest path with parent reconstruction ──────────────────────────
def bfs_path(start_px, start_py, goal_px, goal_py, game_map):
    """Returns list of (px,py) waypoints (pixel centers) using parent reconstruction. Empty if no path."""
    sx, sy = tile(start_px, start_py)
    gx, gy = tile(goal_px, goal_py)
    if sx == gx and sy == gy:
        return [(sx * TILE_SIZE + TILE_SIZE // 2, sy * TILE_SIZE + TILE_SIZE // 2)]
    
    fallback = find_fallback_destination(gx, gy, game_map)
    if fallback is None:
        return []
    gx, gy = fallback

    queue   = deque([(sx, sy)])
    parent  = {(sx, sy): None}
    found   = False
    limit   = 1000

    while queue and limit > 0:
        limit -= 1
        x, y = queue.popleft()
        if x == gx and y == gy:
            found = True
            break
        for dx, dy, cost in DIRS_8:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in parent and not game_map.is_wall(nx, ny):
                # Prevent corner-cutting
                if dx != 0 and dy != 0:
                    if game_map.is_wall(x + dx, y) or game_map.is_wall(x, y + dy):
                        continue
                parent[(nx, ny)] = (x, y)
                queue.append((nx, ny))
                
    if not found:
        return []
        
    # Reconstruct path
    curr = (gx, gy)
    path = []
    while curr is not None:
        path.append(curr)
        curr = parent[curr]
    path.reverse()
    
    waypoints = [(cx * TILE_SIZE + TILE_SIZE // 2, cy * TILE_SIZE + TILE_SIZE // 2) for cx, cy in path]
    return smooth_pixel_path(waypoints, game_map, radius_px=24)


# ── DFS Path — depth-first search path with parent reconstruction ───────────
def dfs_path(start_px, start_py, goal_px, goal_py, game_map):
    """Returns list of (px,py) waypoints using DFS and parent reconstruction."""
    sx, sy = tile(start_px, start_py)
    gx, gy = tile(goal_px, goal_py)
    if sx == gx and sy == gy:
        return [(sx * TILE_SIZE + TILE_SIZE // 2, sy * TILE_SIZE + TILE_SIZE // 2)]
    fallback = find_fallback_destination(gx, gy, game_map)
    if fallback is None:
        return []
    gx, gy = fallback

    stack  = [(sx, sy)]
    parent = {(sx, sy): None}
    found  = False
    limit  = 1000

    while stack and limit > 0:
        limit -= 1
        x, y = stack.pop()
        if x == gx and y == gy:
            found = True
            break
        for dx, dy, cost in DIRS_8:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in parent and not game_map.is_wall(nx, ny):
                # Prevent corner-cutting
                if dx != 0 and dy != 0:
                    if game_map.is_wall(x + dx, y) or game_map.is_wall(x, y + dy):
                        continue
                parent[(nx, ny)] = (x, y)
                stack.append((nx, ny))
                
    if not found:
        return []
        
    curr = (gx, gy)
    path = []
    while curr is not None:
        path.append(curr)
        curr = parent[curr]
    path.reverse()
    
    waypoints = [(cx * TILE_SIZE + TILE_SIZE // 2, cy * TILE_SIZE + TILE_SIZE // 2) for cx, cy in path]
    return smooth_pixel_path(waypoints, game_map, radius_px=24)


# ── DFS — patrol exploration ─────────────────────────────────────────────────
def dfs_patrol_step(current_px, current_py, visited_tiles, game_map, depth=12):
    """Returns next pixel waypoint using DFS exploration. Good for patrolling."""
    sx, sy = tile(current_px, current_py)
    stack   = [(sx, sy, [])]
    seen    = set(visited_tiles) | {(sx, sy)}
    result  = []

    while stack and len(result) < depth:
        x, y, path = stack.pop()
        result = path + [(x, y)]
        for dx, dy, cost in DIRS_8:
            nx, ny = x+dx, y+dy
            if (nx, ny) not in seen and not game_map.is_wall(nx, ny):
                # Prevent corner-cutting
                if dx != 0 and dy != 0:
                    if game_map.is_wall(x + dx, y) or game_map.is_wall(x, y + dy):
                        continue
                seen.add((nx, ny))
                stack.append((nx, ny, result))

    if len(result) > 1:
        nx, ny = result[1]
        return nx*TILE_SIZE + TILE_SIZE//2, ny*TILE_SIZE + TILE_SIZE//2
    return current_px, current_py


# ── A* — optimal with parent reconstruction ──────────────────────────────────
def astar_path(start_px, start_py, goal_px, goal_py, game_map):
    """Returns pixel waypoint list using A* and parent reconstruction."""
    sx, sy = tile(start_px, start_py)
    gx, gy = tile(goal_px, goal_py)
    if sx == gx and sy == gy:
        return [(sx * TILE_SIZE + TILE_SIZE // 2, sy * TILE_SIZE + TILE_SIZE // 2)]
    fallback = find_fallback_destination(gx, gy, game_map)
    if fallback is None:
        return []
    gx, gy = fallback

    # Octile distance heuristic for 8-directional movement
    def h(x, y):
        dx = abs(x - gx)
        dy = abs(y - gy)
        return min(dx, dy) * 1.414 + (max(dx, dy) - min(dx, dy))

    # Priority queue stores (f_score, g_score, x, y)
    open_set = [(h(sx, sy), 0.0, sx, sy)]
    parent = {(sx, sy): None}
    best_g = {(sx, sy): 0.0}
    found = False
    limit = 1000

    while open_set and limit > 0:
        limit -= 1
        _, g, x, y = heapq.heappop(open_set)
        
        if g > best_g.get((x, y), float('inf')):
            continue
            
        if x == gx and y == gy:
            found = True
            break
            
        for dx, dy, cost in DIRS_8:
            nx, ny = x+dx, y+dy
            if not game_map.is_wall(nx, ny):
                # Prevent corner-cutting
                if dx != 0 and dy != 0:
                    if game_map.is_wall(x + dx, y) or game_map.is_wall(x, y + dy):
                        continue
                ng = g + cost
                if ng < best_g.get((nx, ny), float('inf')):
                    best_g[(nx, ny)] = ng
                    parent[(nx, ny)] = (x, y)
                    heapq.heappush(open_set, (ng + h(nx, ny), ng, nx, ny))
                    
    if not found:
        return []
        
    curr = (gx, gy)
    path = []
    while curr is not None:
        path.append(curr)
        curr = parent[curr]
    path.reverse()
    
    waypoints = [(cx * TILE_SIZE + TILE_SIZE // 2, cy * TILE_SIZE + TILE_SIZE // 2) for cx, cy in path]
    return smooth_pixel_path(waypoints, game_map, radius_px=24)


def heuristic_path(start_px, start_py, goal_px, goal_py, game_map):
    """Returns pixel waypoint list using Greedy Best-First Search (Heuristic Search) and parent reconstruction."""
    sx, sy = tile(start_px, start_py)
    gx, gy = tile(goal_px, goal_py)
    if sx == gx and sy == gy:
        return [(sx * TILE_SIZE + TILE_SIZE // 2, sy * TILE_SIZE + TILE_SIZE // 2)]
    fallback = find_fallback_destination(gx, gy, game_map)
    if fallback is None:
        return []
    gx, gy = fallback

    def h(x, y):
        dx = abs(x - gx)
        dy = abs(y - gy)
        return min(dx, dy) * 1.414 + (max(dx, dy) - min(dx, dy))

    open_set = [(h(sx, sy), sx, sy)]
    parent = {(sx, sy): None}
    visited = {(sx, sy)}
    found = False
    limit = 1000

    while open_set and limit > 0:
        limit -= 1
        _, x, y = heapq.heappop(open_set)
        if x == gx and y == gy:
            found = True
            break
        for dx, dy, cost in DIRS_8:
            nx, ny = x+dx, y+dy
            if not game_map.is_wall(nx, ny) and (nx, ny) not in visited:
                # Prevent corner-cutting
                if dx != 0 and dy != 0:
                    if game_map.is_wall(x + dx, y) or game_map.is_wall(x, y + dy):
                        continue
                visited.add((nx, ny))
                parent[(nx, ny)] = (x, y)
                heapq.heappush(open_set, (h(nx, ny), nx, ny))
                
    if not found:
        return []
        
    curr = (gx, gy)
    path = []
    while curr is not None:
        path.append(curr)
        curr = parent[curr]
    path.reverse()
    
    waypoints = [(cx * TILE_SIZE + TILE_SIZE // 2, cy * TILE_SIZE + TILE_SIZE // 2) for cx, cy in path]
    return smooth_pixel_path(waypoints, game_map, radius_px=24)


# ── Heuristic — predict player position ──────────────────────────────────────
def predict_player_pos(player, frames_ahead=45):
    """Predict where player will be in `frames_ahead` frames."""
    spd = math.hypot(player.vx, player.vy)
    if spd < 0.1:
        return player.x, player.y
    return (player.x + player.vx * frames_ahead,
            player.y + player.vy * frames_ahead)
