"""Original exploratory search; prefer scripts/algorithm_repros.py for replay."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import random
from collections import Counter
from GraphAlgo.GraphAlgo import Graph, Node, Edge
from MapParser import MapData
from Common import HubBase, HubType, HubMetadata, ZoneType, ConnectionBase, DroneBase

def graph(n, links, restricted=set(), caps={}, drones=8, priority=set()):
 names=['S']+[f'A{i}' for i in range(n-2)]+['E']
 m=MapData(nb_drones=drones,hubs={x:HubBase(name=x,type=HubType.start_hub if i==0 else HubType.end_hub if i==n-1 else HubType.hub,pos=(i,0),metadata=HubMetadata(zone=ZoneType.restricted if i in restricted else ZoneType.priority if i in priority else ZoneType.normal,max_drones=caps.get(i,1))) for i,x in enumerate(names)},connections=[ConnectionBase(hub_a=names[a],hub_b=names[b],link_capacity=c) for a,b,c in links],drones={i:DroneBase(id=i,coord=(0,0)) for i in range(1,drones+1)},size=(n,1))
 return Graph(m)
def violation(g):
 for t in range(max(len(d.path) for d in g.drons.values())):
  occupancy=Counter(d.path[t] for d in g.drons.values() if len(d.path)>t and isinstance(d.path[t],Node) and d.path[t].type==HubType.hub)
  for node,occ in occupancy.items():
   if occ>node.capacity:return (t,node.name,occ,node.capacity)

if __name__=='__main__':
 random.seed(12)
 for k in range(100000):
  n=random.randrange(4,9)
  links=[(i,j,random.randrange(1,3)) for i in range(n) for j in range(i+1,n) if random.random()<.35]
  restricted=set(i for i in range(1,n-1) if random.random()<.3)
  caps={i:random.randrange(1,3) for i in range(1,n-1)}
  try:
   g=graph(n,links,restricted,caps)
   g.navigate_drones()
  except ValueError:continue
  result=violation(g)
  if result:
   print('case',k,'nodes',n,'links',links,'restricted',restricted,'caps',caps,'VIOLATION',result)
   for d in g.drons.values():print(d.id,[x.name for x in d.path])
   break
