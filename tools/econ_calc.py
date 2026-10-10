# Wayfarer GDD numbers (my calc)
E=0.6; LO=0.4; HI=3.0
def price(base, stock, target):
    r=(target/max(stock,1))**E
    return round(base*min(max(r,LO),HI),1)
res = [ # name, base, daily_prod, daily_cons, target_days
 ("Pine log",4,60,50,5),("Granite block",6,20,15,7),("Fresh fish",5,45,40,2),
 ("Cloudberries",8,12,10,3),("Raw wool",7,15,12,7),("Flax",5,18,15,7),
 ("Clay",3,25,20,7),("Bog iron ore",12,6,5,10),("Birch bark",2,30,20,5),("Wild honey",14,3,3,7)]
print("name base target stock_eq price@50% price@100% price@200% after_player_sells20")
for n,b,p,c,d in res:
    T=c*d
    print(n,b,T,T, price(b,T*0.5,T),price(b,T,T),price(b,T*2,T), price(b,T+20,T))
# rain chain: fresh fish stock 80 target; catch -40% for 2 days, consumption 40
s=80; T=80
for day in range(5):
    prod=45*(0.6 if day in (1,2) else 1.0)
    s=s+prod-40
    print("day",day,"fish stock",round(s),"price",price(5,s,T))
# harder: flood 3 days catch -70%
s=80
for day in range(6):
    prod=45*(0.3 if day in (1,2,3) else 1.0)
    s=max(s+prod-40,0)
    print("flood day",day,"stock",round(s),"price",price(5,s,T))
# audio size
lines=20*140; secs=3.2; kbps=32
print("lines",lines,"MB",round(lines*secs*kbps/8/1024,1))
full=5*60*180
print("full game lines est",full,"MB",round(full*secs*kbps/8/1024,1))
# NPC LOD cpu
tiers={"T0":(12,0.25*1000/1000*1, 5),}
# per-NPC cost ms per update: T0 0.05ms decision@5Hz + anim; T1 0.02@1Hz; T2 0.005@0.1Hz
for n in (20,50,100,250,500):
    t0=min(12,n); t1=min(max(n-12,0),40); t2=max(n-52,0)
    per_s = t0*5*0.05 + t1*1*0.02 + t2*0.1*0.005
    print(n,"NPC ai ms/s",round(per_s,2),"ms/frame@30",round(per_s/30,3))
